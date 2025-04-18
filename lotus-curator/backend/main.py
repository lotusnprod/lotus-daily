import sqlite3
from datetime import datetime

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB = "curation.db"
QLEVER_URL = "https://qlever.cs.uni-freiburg.de/api/wikidata"

# Init DB
conn = sqlite3.connect(DB)
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS curation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT,
    compound_qid TEXT,
    taxon_qid TEXT,
    status TEXT,
    timestamp TEXT
)
""")
c.execute("""
CREATE TABLE IF NOT EXISTS leaderboard (
    user TEXT PRIMARY KEY,
    score INTEGER DEFAULT 0
)
""")
conn.commit()
conn.close()


@app.post("/query")
async def proxy_query(request: Request):
    form = await request.form()
    query = form.get("query")
    if not query:
        return PlainTextResponse("Missing query", status_code=400)

    headers = {
        "Accept": "text/tab-separated-values",
        "User-Agent": "lotus-curator/0.1",
        "Referer": "https://example.org",
    }

    params = {"query": query}
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(QLEVER_URL, params=params, headers=headers)
    except httpx.RequestError as e:
        return PlainTextResponse(f"Error contacting QLever: {e}", status_code=502)

    return PlainTextResponse(r.text, status_code=r.status_code, media_type="text/tab-separated-values")


@app.post("/log")
async def log_curation(data: dict):
    user = data.get("user", "anonymous")
    compound = data.get("compound_qid")
    taxon = data.get("taxon_qid")
    status = data.get("status")

    if not all([compound, taxon, status]):
        return JSONResponse({"error": "Missing fields"}, status_code=400)

    timestamp = datetime.utcnow().isoformat()
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute(
        "INSERT INTO curation (user, compound_qid, taxon_qid, status, timestamp) VALUES (?, ?, ?, ?, ?)",
        (user, compound, taxon, status, timestamp),
    )
    c.execute(
        "INSERT INTO leaderboard(user, score) VALUES (?, 1) ON CONFLICT(user) DO UPDATE SET score = score + 1", (user,)
    )
    conn.commit()
    conn.close()
    return {"ok": True}


@app.get("/leaderboard")
def get_leaderboard():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT user, score FROM leaderboard ORDER BY score DESC LIMIT 10")
    rows = c.fetchall()
    conn.close()
    return {"leaders": [{"user": row[0], "score": row[1]} for row in rows]}
