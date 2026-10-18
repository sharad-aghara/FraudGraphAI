import streamlit as st
from falkordb import FalkorDB
from google import genai
from google.genai import types

# --- Configuration ---
client = genai.Client()
db = FalkorDB(host='localhost', port=6379)
graph = db.select_graph("fraud_network")

# --- Agent Tools ---

def execute_cypher(query: str) -> str:
    """Executes a standard Cypher query against the fraud database."""
    try:
        result = graph.query(query).result_set
        return str(result) if result else "No results found."
    except Exception as e:
        return f"Error executing Cypher: {e}"

def find_shortest_transaction_path(source_account: str, target_account: str) -> str:
    """Uses FalkorDB's shortestPath algorithm to trace money laundering routes."""
    query = f"""
    MATCH (a:Account {{id: '{source_account}'}}), (b:Account {{id: '{target_account}'}})
    RETURN shortestPath((a)-[:TRANSFERRED*]->(b))
    """
    try:
        result = graph.query(query).result_set

        print("result: ", result)
        
        if not result or not result[0] or not result[0][0]:
            return "No path exists between these accounts."
            
        # Extract the Path object
        path_obj = result[0][0]
        
        # Unpack the nodes from the path and get their IDs
        account_path = [node.properties.get('id', 'Unknown') for node in path_obj.nodes()]
        
        # Format it into a clean string for the LLM (e.g., "ACC_81 -> ACC_99")
        readable_path = " -> ".join(account_path)
        
        return f"Suspicious Path Found: {readable_path}"
        
    except Exception as e:
        return f"Error finding path: {e}"

# Register the functions as tools for Gemini
tools = [execute_cypher, find_shortest_transaction_path]

# --- Streamlit UI ---
st.set_page_config(page_title="FraudGraph AI", page_icon="🕵️", layout="wide")
st.title("🕵️ FraudGraph AI: Anti-Money Laundering Agent")
st.markdown("Powered by **FalkorDB Algorithms** & **Gemini**")

st.info("💡 **Feature:** This agent uses FalkorDB's `shortestPath()` algorithm as a native tool to trace complex money laundering layers.")

# Sidebar
with st.sidebar:
    st.header("Investigation Scenarios")
    st.markdown("Try asking the agent to trace a path:")
    st.code("Trace the flow of money of ACC_1 to ACC_19.")
    st.markdown("Or standard Cypher patterns:")
    st.code("Are there any circular transaction loops?")

question = st.text_input("Ask the AI to investigate the transaction graph:")

if st.button("Run Investigation") and question:
    
    with st.spinner("Agent is analyzing the request and selecting tools..."):
        
        # System instructions to guide the agent
        system_instruction = """
        You are an elite Financial Crime Investigator.
        You have access to a FalkorDB graph database with the following schema:
        Nodes: Client, Account, IP_Address
        Edges: (Client)-[:OWNS]->(Account), (Account)-[:TRANSFERRED]->(Account), (Account)-[:LOGGED_IN_FROM]->(IP_Address)
        
        CRITICAL FALKORDB CYPHER RULES:
        1. NEVER use functions like `str()`, `coalesce()`, `nodes(path)`, `relationships(path)`, or list comprehensions like `[n in nodes...]`. 
        
        2. SAFETY LIMITS: ALWAYS append `LIMIT 50` to any `MATCH` query returning nodes or relationships, unless the user is specifically asking for a `count()`.
        
        3. CIRCULAR LOOPS (Smurfing): To find circular money loops, use this exact syntax:
        MATCH (a:Account)-[t1:TRANSFERRED]->(b:Account)-[t2:TRANSFERRED]->(c:Account)-[t3:TRANSFERRED]->(d:Account)
        WHERE a.id = d.id AND a.id <> b.id AND b.id <> c.id
        RETURN a.id, b.id, c.id, t1.amount, t2.amount, t3.amount LIMIT 10
           
        4. SHORTEST PATH TOOL: To trace a flow between TWO specific accounts, you MUST call the `find_shortest_transaction_path` tool. (Note: Do not generate Cypher for shortest path, just call the tool).
           
        5. EMPTY RESULTS: If the tool returns an empty list `[]` or "No results found", inform the user that the requested entity or pattern does not exist in the current graph context. Do not hallucinate data.

        6. AGGREGATIONS: You can use standard Cypher aggregations to find anomalies (e.g., `MATCH (a:Account)-[:LOGGED_IN_FROM]->(ip:IP_Address) RETURN ip.address, count(a) AS acc_count ORDER BY acc_count DESC LIMIT 5`).
        
        For all queries other than shortest path, call `execute_cypher`.
        After receiving the database results, explain the findings clearly to a banking executive.
        """
        
        # Initialize Gemini with tools enabled
        chat = client.chats.create(
            model="gemini-3.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.1,
                tools=tools,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
            )
        )
        
        # Send the user query to the agent
        response = chat.send_message(question)
        
        col1, col2 = st.columns(2)
        
        # Display what the agent did
        with col1:
            st.subheader("1. Agent Tool Execution")
            
            # Check if the model decided to call a tool
            if response.function_calls:
                for tool_call in response.function_calls:
                    st.markdown(f"**Selected Tool:** `{tool_call.name}`")
                    st.markdown(f"**Arguments passed by LLM:**")
                    st.json(tool_call.args)
                    
                    if tool_call.name == "execute_cypher":
                        tool_result = execute_cypher(**tool_call.args)
                    elif tool_call.name == "find_shortest_transaction_path":
                        tool_result = find_shortest_transaction_path(**tool_call.args)
                    
                    st.markdown("**FalkorDB Raw Result:**")
                    st.code(tool_result, language="json")
                    
                    # Send tool result back to Gemini
                    # Send tool result back to Gemini AND explicitly tell it to analyze it
                    final_response = chat.send_message([
                        types.Part.from_function_response(
                            name=tool_call.name,
                            response={"result": tool_result}
                        ),
                        "Analyze this tool result and explain the findings clearly to the user."
                    ])
            else:
                final_response = response
                
        with col2:
            st.subheader("2. Agent Verdict & Explanation")
            if final_response and final_response.text:
                st.success(final_response.text)
            else:
                st.warning("Agent could not generate a textual explanation.")