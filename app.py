import requests
from flask import Flask, render_template, request, redirect, session
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
import hashlib

app = Flask(__name__)
app.secret_key = "secret123"

# MongoDB Connection
client = MongoClient("mongodb://localhost:27017/")
db = client["voting_system"]

voters = db["voters"]
votes = db["votes"]
elections = db["elections"]

# Hash voter identity
def hash_voter_id(voter_id):
    return hashlib.sha256(voter_id.encode()).hexdigest()

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        voter_id = request.form["voter_id"]
        name = request.form["name"]
        age = int(request.form["age"])
        password = generate_password_hash(request.form["password"])

        # Eligibility check
        if age < 18:
            return "Not eligible to vote (Age must be 18+)"

        if voters.find_one({"voter_id": voter_id}):
            return "User already exists!"

        voters.insert_one({
            "voter_id": voter_id,
            "name": name,
            "age": age,
            "password": password,
            "has_voted": False
        })

        return redirect("/")

    return render_template("register.html")

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        voter_id = request.form["voter_id"]
        password = request.form["password"]

        user = voters.find_one({"voter_id": voter_id})

        if user and check_password_hash(user["password"], password):
            session["voter_id"] = voter_id
            return redirect("/vote")
        else:
            return "Invalid Login"

    return render_template("login.html")

@app.route("/vote", methods=["GET", "POST"])
def vote():
    if "voter_id" not in session:
        return redirect("/")

    voter_id = session["voter_id"]
    voter = voters.find_one({"voter_id": voter_id})

    if voter["has_voted"]:
        return "You already voted!"

    election = elections.find_one({"status": "active"})

    if not election:
        return "No active election found!"

    eligible_candidates = [c["name"] for c in election["candidates"] if c["age"] >= 21]

    if request.method == "POST":
        candidate = request.form["candidate"]
        voter_hash = hash_voter_id(voter_id)

        try:
            ip = request.remote_addr
            device_id = "D1" 

            fraud_response = requests.get(
                "http://127.0.0.1:5002/fraud-check",
                params={
                    "voter_id": voter_id,
                    "ip": ip,
                    "device_id": device_id
                }
            )

        fraud_data = fraud_response.json()

        if fraud_data["status"] == "suspicious":
            return render_template(
                "vote.html",
                candidates=eligible_candidates,
                error=f"Fraud Detected : {fraud_data['reason']}"
            )

        votes.insert_one({
            "voter_hash": voter_hash,
            "candidate": candidate
        })

        voters.update_one(
            {"voter_id": voter_id},
            {"$set": {"has_voted": True}}
        )

        return redirect("/result")

        except:
            return "Duplicate Vote!"

    return render_template("vote.html", candidates=eligible_candidates)

# ---------------- RESULT ----------------
@app.route("/result")
def result():
    results = votes.aggregate([
        {"$group": {"_id": "$candidate", "count": {"$sum": 1}}}
    ])

    data = {r["_id"]: r["count"] for r in results}
    return render_template("result.html", data=data)

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
