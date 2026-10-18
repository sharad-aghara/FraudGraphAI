from falkordb import FalkorDB
import random
from datetime import datetime, timedelta

# Connect to FalkorDB
db = FalkorDB(host='localhost', port=6379)
graph = db.select_graph("fraud_network")
print("Clearing old data...")
graph.query("MATCH (n) DELETE n")

print("Generating realistic banking data...")

# 1. Generate 50 Normal Clients, Accounts, and IPs
for i in range(1, 51):
    ip = f"192.168.1.{random.randint(10, 255)}"
    graph.query(f"""
        MERGE (c:Client {{id: 'C_{i}', name: 'User_{i}', risk_score: 'low'}})
        MERGE (a:Account {{id: 'ACC_{i}', balance: {random.randint(1000, 15000)}}})
        MERGE (ip:IP_Address {{address: '{ip}'}})
        MERGE (c)-[:OWNS]->(a)
        MERGE (a)-[:LOGGED_IN_FROM]->(ip)
    """)

# 2. Inject Normal Random Transactions
for _ in range(100):
    sender = f"ACC_{random.randint(1, 50)}"
    receiver = f"ACC_{random.randint(1, 50)}"
    amount = random.randint(10, 500)
    if sender != receiver:
        graph.query(f"MATCH (s:Account {{id: '{sender}'}}), (r:Account {{id: '{receiver}'}}) CREATE (s)-[:TRANSFERRED {{amount: {amount}}}]->(r)")

# 3. INJECT FRAUD PATTERN A: "Smurfing / Structuring Ring"
# Accounts 91, 92, and 93 are sending money in a circle just under the $10k reporting limit.
print("Injecting Fraud Pattern A: Smurfing Ring...")
graph.query("""
    CREATE (a1:Account {id: 'ACC_91'}), (a2:Account {id: 'ACC_92'}), (a3:Account {id: 'ACC_93'})
    CREATE (a1)-[:TRANSFERRED {amount: 9900}]->(a2)
    CREATE (a2)-[:TRANSFERRED {amount: 9950}]->(a3)
    CREATE (a3)-[:TRANSFERRED {amount: 9800}]->(a1)
""")

# 4. INJECT FRAUD PATTERN B: "Account Takeover via Shared IP"
# Accounts 81, 82, and 83 all suddenly log in from the same weird IP and funnel money to Account 99.
print("Injecting Fraud Pattern B: Account Takeover Funnel...")
graph.query("""
    MERGE (ip:IP_Address {address: '10.55.22.111', flagged: 'true'})
    MERGE (boss:Account {id: 'ACC_99'})
    MERGE (a1:Account {id: 'ACC_81'}) MERGE (a2:Account {id: 'ACC_82'}) MERGE (a3:Account {id: 'ACC_83'})
    MERGE (a1)-[:LOGGED_IN_FROM]->(ip) MERGE (a2)-[:LOGGED_IN_FROM]->(ip) MERGE (a3)-[:LOGGED_IN_FROM]->(ip)
    CREATE (a1)-[:TRANSFERRED {amount: 5000}]->(boss)
    CREATE (a2)-[:TRANSFERRED {amount: 5000}]->(boss)
    CREATE (a3)-[:TRANSFERRED {amount: 5000}]->(boss)
""")

print("Data generation complete! The graph is ready for investigation.")