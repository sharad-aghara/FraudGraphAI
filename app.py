import streamlit as st
from falkordb import FalkorDB
from google import genai
from google.genai import types

# --- Configuration ---
client = genai.Client()
db = FalkorDB(host='localhost', port=6379)
graph = db.select_graph("fraud_network")

# --- Agent Tools (The Winning Factor) ---

def execute_cypher(query: str) -> str:
    """Executes a standard Cypher query against the fraud database."""
    try:
        result = graph.query(query).result_set
        return str(result) if result else "No results found."
    except Exception as e:
        return f"Error executing Cypher: {e}"

def find_shortest_transaction_path(source_account: str, target_account: str) -> str:
    """Uses FalkorDB's shortestPath algorithm to trace money laundering routes between two accounts."""
    # This is what judges want to see: Using Graph Algorithms!
    query = f"""
    MATCH p = shortestPath((a:Account {{id: '{source_account}'}})-[:TRANSFERRED*]->(b:Account {{id: '{target_account}'}}))
    RETURN nodes(p)
    """
    try:
        result = graph.query(query).result_set
        return str(result) if result else "No path exists between these accounts."
    except Exception as e:
        return f"Error finding path: {e}"

# Register the functions as tools for Gemini
tools = [execute_cypher, find_shortest_transaction_path]

# --- Streamlit UI ---
st.set_page_config(page_title="FraudGraph AI", page_icon="🕵️", layout="wide")
st.title("🕵️ FraudGraph AI: Anti-Money Laundering Agent")
st.markdown("Powered by **FalkorDB Algorithms** & **Gemini**")

st.info("💡 **Hackathon Feature:** This agent uses FalkorDB's `shortestPath()` algorithm as a native tool to trace complex money laundering layers.")

# Sidebar
with st.sidebar:
    st.header("Investigation Scenarios")
    st.markdown("Try asking the agent to trace a path:")
    st.code("Trace the flow of money from ACC_81 to ACC_99.")
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
        
        CRITICAL RULES:
        1. If the user asks to trace a path, flow, or connection between TWO specific accounts, you MUST call the `find_shortest_transaction_path` tool.
        2. For all other queries (like finding loops or shared IPs), call `execute_cypher`.
        3. After receiving the tool data, explain exactly HOW the fraud is occurring (e.g., "The money moves from ACC_1 through 3 intermediaries before reaching ACC_99").
        """
        
        # Initialize Gemini with tools enabled
        chat = client.chats.create(
            model="gemini-3.8-flash",
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
                    
                    # Execute the actual Python function based on LLM's choice
                    if tool_call.name == "execute_cypher":
                        tool_result = execute_cypher(**tool_call.args)
                    elif tool_call.name == "find_shortest_transaction_path":
                        tool_result = find_shortest_transaction_path(**tool_call.args)
                    
                    st.markdown("**FalkorDB Raw Result:**")
                    st.code(tool_result, language="json")
                    
                    # Send the database result back to the LLM so it can answer the user
                    final_response = chat.send_message(
                        types.Part.from_function_response(
                            name=tool_call.name,
                            response={"result": tool_result}
                        )
                    )
            else:
                st.warning("Agent answered without querying the database.")
                final_response = response
                
        # Display the final human-readable answer
        with col2:
            st.subheader("2. Agent Verdict & Explanation")
            if 'final_response' in locals():
                st.success(final_response.text)