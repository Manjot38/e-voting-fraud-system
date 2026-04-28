const express = require("express");
const mongoose = require("mongoose");
const axios = require("axios");
const app = express();

// Middleware
app.use(express.json());

// Model
const Vote = require("./models/Vote");

// Home
app.get("/", (req, res) => {
  res.send("Server running 🚀");
});

// ✅ Save vote with fraud detection
app.post("/vote", async (req, res) => {
  try {
    app.post("/vote", async (req, res) => {
  try {
    const { voterId, candidate, region } = req.body;
    const fraudResponse = await axios.get(
      "http://127.0.0.1:5002/fraud-check",
      {
        params: {
          voter_id: voterId,
          ip: req.ip,
          device_id: "D1"
        }
      }
    );

    const fraudData = fraudResponse.data;

    if (fraudData.status === "suspicious") {
      return res.send(`Fraud Detected: ${fraudData.reason}`);
    }

    // STEP 3: CHECK DUPLICATE (your old logic)
    const existingVote = await Vote.findOne({ voterId });

    if (existingVote) {
      return res.send("Already voted");
    }

    // 🔹 STEP 4: SAVE VOTE
    const vote = new Vote({
      voterId,
      candidate,
      region,
      fraudStatus: fraudData.status   
    });

    await vote.save();

    res.send("Vote saved successfully");

  } catch (err) {
    res.status(500).send(err.message);
  }
});
  } catch (err) {
    res.status(500).send(err);
  }
});

// ✅ Test route (safe)
app.get("/testvote", async (req, res) => {
  try {
    const existingVote = await Vote.findOne({ voterId: "101" });

    if (existingVote) {
      return res.send("❌ Test voter already voted");
    }

    const vote = new Vote({
      voterId: "101",
      candidate: "A",
      region: "Delhi"
    });

    await vote.save();
    res.send("✅ Test vote saved");
  } catch (err) {
    res.status(500).send(err);
  }
});

// ✅ View all votes
app.get("/votes", async (req, res) => {
  try {
    const votes = await Vote.find();
    res.json(votes);
  } catch (err) {
    res.status(500).send(err);
  }
});

// ✅ Region-wise stats (for dashboard)
app.get("/stats", async (req, res) => {
  try {
    const stats = await Vote.aggregate([
      { $group: { _id: "$region", count: { $sum: 1 } } }
    ]);
    res.json(stats);
  } catch (err) {
    res.status(500).send(err);
  }
});

// ✅ Clear all votes (optional for testing)
app.get("/clear", async (req, res) => {
  await Vote.deleteMany({});
  res.send("All votes cleared");
});

// DB connection
mongoose.connect("mongodb://127.0.0.1:27017/electionDB")
.then(() => console.log("DB connected"))
.catch(err => console.log(err));

// Start server
app.listen(5000, () => {
  console.log("Server started on port 5000");
});
