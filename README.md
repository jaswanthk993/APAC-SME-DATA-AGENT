# 🤖 SME Data Copilot — AI Business Intelligence

Multilingual AI Data Assistant for SMEs. Ask business questions in **any language** — the system queries your AlloyDB database and returns insights in the same language.

## 🏗️ Architecture

```
User Query (Any Language)
         ↓
🌐 Translation Agent (Gemini) — Detect & translate to English
         ↓
🔍 SQL Agent (Gemini + AlloyDB) — Generate & execute SQL
         ↓
✍️ Response Agent (Gemini) — Summarize & translate back
         ↓
📡 NDJSON Stream → 🎨 Frontend UI
```

## ⚙️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python 3.11, FastAPI |
| LLM | Google Gemini 2.0 Flash |
| Database | AlloyDB (PostgreSQL) |
| Frontend | Vanilla HTML/CSS/JS |
| Charts | Canvas API |
| Streaming | NDJSON |

## 🚀 Quick Start

### 1. Set up environment variables

```bash
cp .env.example .env
# Edit .env with your credentials
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Initialize database

Run `backend/seed.sql` against your AlloyDB instance.

### 4. Start the server

```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8080
```

### 5. Open the UI

Navigate to `http://localhost:8080`

## 📡 API Endpoints

### `GET /health`
Returns system health and agent status.

### `POST /api/chat`
Accepts a `{ "message": "..." }` body and returns an NDJSON stream.

## 🔐 Security

- **SQL injection prevention**: Only SELECT/WITH queries allowed
- **Keyword blocking**: INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE blocked
- **Read-only transactions**: All queries run in read-only mode
- **Environment variables**: No hardcoded credentials

## 🌏 Supported Languages

English, Hindi, Japanese, Chinese, Korean, Vietnamese, Thai, Malay, Indonesian, Filipino, Tamil, Telugu, Bengali, French, German, Spanish, Arabic, and more.
