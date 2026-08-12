const express = require("express");
const fs = require("fs/promises");
const path = require("path");

const app = express();
const port = process.env.PORT || 3000;
const dataFilePath = path.join(__dirname, "data", "admissions.json");

app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static(__dirname));

async function readAdmissions() {
    try {
        const data = await fs.readFile(dataFilePath, "utf8");
        return JSON.parse(data);
    } catch (error) {
        if (error.code === "ENOENT") {
            return [];
        }

        throw error;
    }
}

async function saveAdmissions(records) {
    await fs.mkdir(path.dirname(dataFilePath), { recursive: true });
    await fs.writeFile(dataFilePath, JSON.stringify(records, null, 2), "utf8");
}

app.post("/api/admissions", async (req, res) => {
    try {
        const { fullName, emailAddress, courseApplied, phoneNumber, permanentAddress } = req.body;

        if (!fullName || !emailAddress || !courseApplied || !phoneNumber) {
            return res.status(400).json({
                message: "fullName, emailAddress, courseApplied and phoneNumber are required."
            });
        }

        const record = {
            id: Date.now(),
            fullName: String(fullName).trim(),
            emailAddress: String(emailAddress).trim(),
            courseApplied: String(courseApplied).trim(),
            phoneNumber: String(phoneNumber).trim(),
            permanentAddress: String(permanentAddress || "").trim(),
            createdAt: new Date().toISOString()
        };

        const admissions = await readAdmissions();
        admissions.push(record);
        await saveAdmissions(admissions);

        return res.status(201).json({
            message: "Application submitted successfully.",
            data: record
        });
    } catch (error) {
        return res.status(500).json({
            message: "Server error while saving admission form.",
            error: error.message
        });
    }
});

app.get("/api/admissions", async (_req, res) => {
    try {
        const admissions = await readAdmissions();
        return res.json({ count: admissions.length, data: admissions });
    } catch (error) {
        return res.status(500).json({
            message: "Server error while reading admissions.",
            error: error.message
        });
    }
});

app.get("/health", (_req, res) => {
    res.json({ status: "ok" });
});

app.listen(port, () => {
    console.log(`Server running at http://localhost:${port}`);
});
