from flask import Flask, request, jsonify
from neo4j import GraphDatabase

app = Flask(__name__)

driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "qwerty789")
)

@app.route('/')
def home():
    return "Fraud Detection API Running ✅"

@app.route('/fraud-check')
def fraud_check_get():
    try:
        voter_id = request.args.get('voter_id')
        ip = request.args.get('ip')
        device = request.args.get('device_id')
        if not voter_id or not ip or not device:
            return "Missing parameters "
        with driver.session() as session:
            session.run("""
            MERGE (v:Voter {id:$voter})
            MERGE (ip:IP {address:$ip})
            MERGE (d:Device {id:$device})

            MERGE (v)-[:USED_IP]->(ip)
            MERGE (v)-[:USED_DEVICE]->(d)
            """, voter=voter_id, ip=ip, device=device)
    
        # Check IP fraud
            ip_result = session.run("""
            MATCH (ip:IP)<-[:USED_IP]-(v:Voter)
            WHERE ip.address = $ip
            RETURN COUNT(v) AS count
            """, ip=ip)

            ip_count = ip_result.single()["count"]

            device_result = session.run("""
            MATCH (d:Device)<-[:USED_DEVICE]-(v:Voter)
            WHERE d.id = $device
            RETURN COUNT(v) AS count
            """, device=device)
        
            device_count = device_result.single()["count"]

        # Decision
            if ip_count > 2:
                reason = "Multiple votes from same IP"
            elif device_count > 2:
                reason = "Multiple votes from same device"
            else:
                reason = "No fraud"

            return jsonify({
                "status": "suspicious" if ip_count > 2 or device_count > 2 else "clean",
                "reason": reason,
                "ip_count": ip_count,
                "device_count": device_count
            })
    except Exception as e:
        return str(e)        

if __name__ == '__main__':
    app.run(port=5002)