# Browser-Use Agent — Gemini Edition

Open-source browser automation agent powered by [browser-use](https://github.com/browser-use/browser-use) and Google Gemini. A stronger alternative to k3-mariner / Project Mariner.

Give it a task in plain English. It opens a browser, navigates the web, and completes it autonomously.

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
python -m pip install browser-use==0.1.40 langchain-google-genai==2.1.12 python-dotenv playwright
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

## Example tasks

- `Go to wikipedia.org and tell me the main topic on the homepage today`
- `Search Google for the latest iPhone price in Australia`
- `Go to bom.gov.au and tell me the weather in Melbourne`
- `Go to news.ycombinator.com and find the top post today`

---

## Notes

- Your `.env` file is gitignored — your API key will NOT be committed.
- The agent uses `gemini-2.5-flash` by default.
- On Ubuntu/server (no GUI), `headless=True` is set in `agent.py` — the browser runs invisibly in the background.
- On Windows, `headless=False` lets you watch the browser navigate in real time.
- The `RuntimeError: Event loop is closed` message on Windows at the end is harmless — ignore it.
- Free Gemini tier has rate limits — the agent will retry automatically if it hits them.
