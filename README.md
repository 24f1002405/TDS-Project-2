---
title: TDS Project 2
emoji: ⚡
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
license: mit
---

# 🚀 AI Data Analyst

An **AI-powered data analyst** built with **FastAPI** and **Google Gemini API**.
It accepts natural language questions and supporting files, then returns structured JSON answers, including data analysis and charts encoded as **base64 images**.

This app is designed for:

* 📊 Automated data analysis
* 📈 Chart generation (base64 PNGs)

---

## 👤 Author & Metadata

* **Name:** Rajat Raj Singh
* **Roll No:** 24F1002405
* **Deployment Server:** [https://24f1002405-tds-project-2.hf.space](https://24f1002405-tds-project-2.hf.space)
* **License:** [MIT](./LICENSE)

---

## ⚙️ Features

* ⚡ **FastAPI async server** – Handles multiple requests concurrently with high performance.
* 📝 **Per-request server logging** – Detailed logs for each request with request ID, client info, execution status, and timing.
* 🧠 **Powered by Gemini 2.5 Pro** – Leverages Google’s latest LLM for reasoning, analysis, and code generation.
* 🔀 **Load balancing** – Rotates across multiple Gemini API keys for improved stability and performance.
* 📂 **File handling** – Accepts both text (e.g., CSV, TXT, Markdown) and binary (e.g., images, PDFs) files.
* 🤖 **Dynamic code generation** – LLM generates Python code dynamically to answer questions.
* 🔄 **Automatic error correction** – Re-prompts Gemini to fix code when execution errors occur.
* 🔐 **Encrypted API key management** – API keys are encrypted locally and decrypted securely at runtime.

---

## 🛠️ Setup & Installation

### 1. Clone the repository

```bash
git clone https://github.com/24f1002405/TDS-Project-2.git
cd TDS-Project-2
```

### 2. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 🔐 API Key Encryption Setup

Before running locally or deploying, **encrypt your Gemini API keys**.

### 1. Store gemini api keys

Store all your gemini api keys inside `gemini-keys.txt`, one per line.

```txt
key1
key2
.
.
.
```

### 2. Encrypt gemini api keys

Run `encrypt-keys.py`, passing the file name containing keys.

```bash
python encrypt-keys.py gemini-keys.txt
```

- This will encrypt all the keys inside `gemini-keys.txt` and prints the encryption key on the console.
- **Save this key securely** and set it as an environment variable:

```bash
export ENCRYPTION_KEY="your-generated-key"
```

> ✅ Do **not** commit or push unencrypted keys.

## ▶️ Running the App

Start the FastAPI app using **Uvicorn**:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

API will be available at:

```
http://localhost:8000
```

---

## 📤 Example Request

### Request

```bash
curl "http://localhost:8000" \
     -F "questions.txt=@network.md" \
     -F "edges.csv=@edges.csv"
```

> All requests necessarily include `questions.txt`, with 0 or more supporting files.

### Example `network.md`

```md
Use the undirected network in `edges.csv`.

Return a JSON object with keys:
- `edge_count`: number
- `highest_degree_node`: string
- `average_degree`: number
- `density`: number
- `shortest_path_alice_eve`: number
- `network_graph`: base64 PNG string under 100kB
- `degree_histogram`: base64 PNG string under 100kB
```

### Example `edges.csv`

```csv
source,target
Alice,Bob
Alice,Carol
Bob,Carol
Bob,David
Bob,Eve
Carol,David
David,Eve
```

---

## 📥 Example Response

```json
{
    "edge_count": 7,
    "highest_degree_node": "Bob",
    "average_degree": 2.8,
    "density": 0.7,
    "shortest_path_alice_eve": 2,
    "network_graph": "iVBORw0KGgo...(response truncated)"
}
```

---

## 📜 License

This project is licensed under the **MIT License** – see the [LICENSE](./LICENSE) file for details.
