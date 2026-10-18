import streamlit as st
from falkordb import FalkorDB
from google import genai
import os

# --- Configuration ---
# Ensure your API key is in your environment: export GEMINI_API_KEY="your_key"
client = genai.Client()
db = FalkorDB(host='localhost', port=6379)
graph = db.select_graph("fraud_network")

SCHEMA = """
Nodes: 
- Client (id, name, risk_score)
- Account (id, balance)
- IP_Address (address, flagged)
Relationships: 
- (Client)-[:OWNS]->(Account)
- (Account)-[:TRANSFERRED {amount}]->(Account)
- (Account)-[:LOGGED_IN_FROM]->(IP_Address)

CRITICAL CYPHER RULES FOR FALKORDB:
- To find circular money loops (Smurfing): MATCH (a)-[t1:TRANSFERRED]->(b)-[t2:TRANSFERRED]->(c)-[t3:TRANSFERRED]->(a) RETURN a.id, b.id, c.id
- To find shared IP funnels: MATCH (a1:Account)-[:LOGGED_IN_FROM]->(ip:IP_Address)<-[:LOGGED_IN_FROM]-(a2:Account), (a1)-[t1:TRANSFERRED]->(boss:Account), (a2)-[t2:TRANSFERRED]->(boss) RETURN ip.address, boss.id
"""

def generate_cypher(question):
    prompt = f"Schema: {SCHEMA}\n\nUser Question: {question}\n\nWrite ONLY the raw Cypher query to answer this. No markdown formatting, no explanation."
    response = client.models.generate_content(model="gemini-3.8-flash", contents=prompt)
    return response.text.strip().replace("```cypher", "").replace("```", "")

def analyze_results(question, db_data):
    prompt = f"You are a Senior Financial Crime Analyst. \nQuestion: {question}\nRaw Database Results: {db_data}\n\nExplain these findings professionally to a banking executive. Highlight any money laundering, smurfing (circular loops), or account takeovers (shared IPs). Be concise but explain *why* it is suspicious based on the connections."
    response = client.models.generate_content(model="gemini-3.8-flash", contents=prompt)
    return response.text

# --- Streamlit UI ---
st.set_page_config(page_title="FraudGraph AI", page_icon="🕵️", layout="wide")
st.title("🕵️ FraudGraph AI: Anti-Money Laundering Agent")
st.markdown("Powered by **FalkorDB** & **Gemini 3.8 Flash**")

# Sidebar
with st.sidebar:
    st.header("Suggested Investigations")
    st.info("Try asking:")
    st.code("Are there any circular transaction loops?")
    st.code("Do any multiple accounts share the same IP address and send money to a single account?")
    st.code("Show me the transaction history for ACC_99.")

# Chat Interface
question = st.text_input("Ask the AI to investigate the transaction graph:")

if st.button("Run Investigation") and question:
    col1, col2 = st.columns(2)
    
    with st.spinner("Agent is formulating graph query..."):
        cypher = generate_cypher(question)
        
        with col1:
            st.subheader("1. Agent Query Generation")
            st.markdown("The LLM translates intent into this multi-hop Cypher query:")
            st.code(cypher, language="cypher")
            
    with st.spinner("Traversing FalkorDB Graph..."):
        try:
            result = graph.query(cypher).result_set
            
            with col1:
                st.subheader("2. Raw Graph Output")
                if not result:
                    st.warning("No suspicious patterns found matching that query.")
                else:
                    st.write(result)
                    
            if result:
                with st.spinner("Agent is analyzing the graph structures..."):
                    analysis = analyze_results(question, result)
                    
                    with col2:
                        st.subheader("3. Agent Verdict & Explanation")
                        st.success(analysis)
        except Exception as e:
            st.error(f"Graph Error: {e}")