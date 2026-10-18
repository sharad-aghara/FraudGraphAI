# 🕵️ FraudGraph AI: Agentic Financial Crime Investigator
 
**Track:** Track 01 - Agents That Act on Connected Data

## 📌 Project Overview
Legacy banking systems rely on relational databases (SQL) that struggle to identify complex, multi-hop financial crimes like smurfing, circular money laundering, and account takeovers. 

**FraudGraph AI** is an intelligent AI Agent powered by **Gemini 3.5 Flash** and **FalkorDB**. By mapping financial transactions as a graph, the agent can actively traverse relationships, utilize native graph algorithms, and explain its investigative reasoning to human analysts in real-time.

### ✨ Key Features (Hackathon Track Alignments)
* **Multi-Hop Reasoning:** Dynamically generates Cypher queries to detect circular transaction loops (Smurfing).
* **Agentic Tool Use (MCP Concept):** The agent autonomously decides whether to write standard Cypher or trigger native database algorithms based on the user's intent.
* **FalkorDB Algorithms:** Utilizes FalkorDB's native `shortestPath()` algorithm as a tool to trace the exact flow of illicit funds across numerous intermediary accounts.
* **Explainable AI:** Traces decisions directly back to graph nodes and edges, providing clear, factual explanations of the fraud topology.

---

## 🕸️ Graph Data Model Schema
* **Nodes:** `Client`, `Account`, `IP_Address`
* **Relationships:** 
  * `(Client)-[:OWNS]->(Account)`
  * `(Account)-[:TRANSFERRED {amount}]->(Account)`
  * `(Account)-[:LOGGED_IN_FROM]->(IP_Address)`

---

## 🚀 Local Setup & Installation

Follow these steps to run the FraudGraph AI agent locally.

### 1. Start FalkorDB
You must have Docker installed and running. Spin up the FalkorDB container:
```bash
docker run -p 6379:6379 -p 3000:3000 falkordb/falkordb:latest
```
*(You can view the database visualizer at `http://localhost:3000`)*

### 2. Set Up Python Virtual Environment
Open a new terminal window in your project directory and create a virtual environment:

**For Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**For macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
Ensure your virtual environment is active, then install the required packages:
```bash
pip install falkordb google-genai streamlit
```

### 4. Configure API Key
Export your Gemini API Key to your environment variables.
**Windows (PowerShell):**
```powershell
$env:GEMINI_API_KEY="your_api_key_here"
```
**macOS/Linux:**
```bash
export GEMINI_API_KEY="your_api_key_here"
```

### 5. Generate the Synthetic Graph Data
Run the ingestion script. This script populates FalkorDB with dozens of normal clients, accounts, and transactions, while secretly injecting complex multi-hop fraud rings (Smurfing and Shared-IP Takeovers).
```bash
python generate_data.py
```

### 6. Launch the AI Agent Interface
Start the Streamlit application:
```bash
streamlit run app.py
```

---

## 🧪 Example Investigations to Try
Once the web UI is running, try asking the agent these exact questions to see it utilize different tools and graph traversals:

1. **Test Standard Cypher & Anomaly Detection:**
   > *"Are there any circular transaction loops?"*
2. **Test FalkorDB Graph Algorithms (Shortest Path):**
   > *"Trace the flow of money from ACC_1 to ACC_19."*
3. **Test Shared-IP Account Takeover Detection:**
   > *"Do any multiple accounts share the same IP address and funnel money to a single account?"*