# Browser-Use Agent — Gemini Edition

Open-source browser automation agent powered by [browser-use](https://github.com/browser-use/browser-use) and Google Gemini. A stronger alternative to k3-mariner / Project Mariner.

Give it a task in plain English. It opens a real browser, navigates the web, and completes it autonomously — with a **tiered trust/autonomy model** so different websites get the right level of care.

---

## Architecture

The agent now uses a policy-driven architecture that classifies every target domain into a browsing tier:

| Tier | Description | Profile | Headless | Manual checkpoint |
|------|-------------|---------|----------|-------------------|
| 1 | High-value, stateful, anti-bot-sensitive (e.g. Discord) | Persistent (per-site) | No | Yes — required |
| 2 | General web; reliability matters | Shared | Configurable | Optional |
| 3 | Disposable/generic public web | None (ephemeral) | Yes | No |

### New modules

| File | Purpose |
|------|---------|
| `site_policies.py` | Loads `policies/default.yaml` and resolves the effective policy for any domain |
| `policies/default.yaml` | Default policy config (Discord = Tier 1; all other sites = Tier 3 default) |
| `session_manager.py` | Manages persistent browser profile directories under `.profiles/` |
| `challenge_detector.py` | Heuristic CAPTCHA / bot-challenge / login-wall detection |
| `manual_checkpoint.py` | Human-in-the-loop pause/resume flow for protected sites |
| `agent_result.py` | Structured outcome reporting (status enum + output + reason) |

---

## Requirements

- Python 3.12 (not 3.13 or 3.14 — they're incompatible with current deps)
- Git
- A free Gemini API key → https://aistudio.google.com/apikey

---

## Setup — Ubuntu / Mac / WSL2

### 1. Clone the repo

```bash
git clone https://github.com/innovative-vision/Project_Mariner_Scrapev2.git
cd Project_Mariner_Scrapev2
```

### 2. Install dependencies

```bash
pip3 install -r requirements.txt --break-system-packages
```

### 3. Install Playwright browser

```bash
playwright install chromium --with-deps
```

### 4. Add your API key

```bash
cp .env.example .env
nano .env
```
Replace `your_api_key_here` with your Gemini key. Save with Ctrl+O → Enter → Ctrl+X.

### 5. Run

```bash
python3 agent.py
```

You'll be prompted to type a task.  
You can also pass the task as a command-line argument:

```bash
python3 agent.py "Go to wikipedia.org and summarise the article on black holes"
```

---

## Setup — Windows

### 1. Install Python 3.12
Download from https://www.python.org/downloads/release/python-3129/  
**Tick "Add Python to PATH" during install.**

### 2. Clone the repo
Open PowerShell:
```powershell
cd Desktop
git clone https://github.com/innovative-vision/Project_Mariner_Scrapev2.git
cd Project_Mariner_Scrapev2
```

### 3. Install dependencies
```powershell
python -m pip install -r requirements.txt
```

### 4. Install Playwright browser
```powershell
python -m playwright install chromium
```

### 5. Add your API key
```powershell
notepad .env
```
Type `GEMINI_API_KEY=your_key_here`, save and close Notepad.

### 6. Run
```powershell
python agent.py
```

---

## Customising site policies

Edit `policies/default.yaml` to add or modify site policies.

```yaml
policies:
  # Tier 1 example — persistent profile, manual checkpoints, no headless
  discord.com:
    tier: 1
    access_mode: browser_manual_only
    persistent_profile: true
    headless_allowed: false
    manual_checkpoint: true
    challenge_strictness: strict
    resource_blocking: false

  # Add your own Tier 1 site here:
  # mysite.com:
  #   tier: 1
  #   access_mode: browser_manual_only
  #   persistent_profile: true
  #   headless_allowed: false
  #   manual_checkpoint: true
  #   challenge_strictness: strict
  #   resource_blocking: false

  # Global default (applies to every other site)
  __default__:
    tier: 3
    access_mode: browser
    persistent_profile: false
    headless_allowed: true
    manual_checkpoint: false
    challenge_strictness: basic
    resource_blocking: true
```

---

## Example tasks

- `Go to wikipedia.org and tell me the main topic on the homepage today`
- `Search Google for the latest iPhone price in Australia`
- `Go to bom.gov.au and tell me the weather in Melbourne`
- `Go to news.ycombinator.com and find the top post today`

---

## Gemini Shadow Courtroom — Backend

An optional FastAPI backend that logs every Gemini exchange, fans it out to three independent AI judges, writes a courtroom transcript to Google Docs, and appends hourly summaries to Google Sheets.

### Architecture

```
POST /log  ←─── Chrome extension (or curl)
    │
    ├── Google Docs  ── Courtroom transcript (prompt + response + 3 judge opinions)
    ├── OpenRouter   ── Judge Dmitri · The Architect · Agent Zero (parallel)
    └── Scheduler    ── Every 4 h → Gemini Flash summary → Google Sheets row
```

All integrations degrade gracefully — the server starts and `/health` returns `200` even with zero optional keys set.

### Step 1 — Heartbeat test (Google Docs only)

```bash
cd backend
pip install -r requirements.txt
```

Add to `.env`:
```
GOOGLE_CREDENTIALS_JSON=<base64-encoded service account JSON>
GDOC_ID=<your doc id from the URL>
```

Start the server:
```bash
uvicorn backend.main:app --reload
```

Heartbeat test:
```bash
curl -X POST http://localhost:8000/log \
  -H "Content-Type: application/json" \
  -d '{"prompt":"What is 2+2?","response":"2+2 equals 4."}'
```

Open your Google Doc — you should see the exchange appended. ✓

### Step 2 — Add judges

Add to `.env`:
```
OPENROUTER_API_KEY=<your key from openrouter.ai>
```

Restart the server. The same `curl` call now returns three judge opinions and writes them into the Doc.

### Step 3 — Summaries to Sheets

Add to `.env`:
```
GSHEET_ID=<your sheet id from the URL>
SUMMARY_INTERVAL_HOURS=4   # optional, default 4
```

The scheduler fires automatically every N hours, sends buffered exchanges to Gemini Flash, and appends a row to your Sheet. Empty window → logs "Nil".

### Deploy to Railway

1. Connect this repo to Railway.
2. Set all env vars in the Railway dashboard.
3. Railway uses `railway.toml` to start `uvicorn backend.main:app --host 0.0.0.0 --port $PORT` automatically.

### Google credentials setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project → enable **Google Docs API** + **Google Sheets API**
3. Create a **Service Account** → download the JSON key file
4. Share your Google Doc and Sheet with the service account email (Editor)
5. Base64-encode the JSON: `base64 -w 0 credentials.json`
6. Paste the result into `GOOGLE_CREDENTIALS_JSON` in `.env`

---

## Notes

- Your `.env` file is gitignored — your API key will NOT be committed.
- The agent uses `gemini-2.5-flash` by default.
- Persistent browser profiles are stored in `.profiles/` (gitignored).
- On Ubuntu/server (no GUI), Tier 3 sites run `headless=True` automatically.
- On Windows (and Tier 1 sites), `headless=False` lets you watch the browser.
- The `RuntimeError: Event loop is closed` message on Windows at the end is harmless — ignore it.
- Free Gemini tier has rate limits — the agent will retry automatically if it hits them.
