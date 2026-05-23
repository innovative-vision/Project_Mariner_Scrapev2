# Browser-Use Agent — Gemini Edition

Open-source browser automation agent powered by [browser-use](https://github.com/browser-use/browser-use) and Google Gemini. A stronger alternative to k3-mariner / Project Mariner.

Give it a task in plain English. It opens a real browser, navigates the web, and completes it autonomously.

---

## Requirements

- Python 3.11+
- Git
- Google Chrome (installed on your system)
- A free Gemini API key → https://aistudio.google.com/apikey

---

## Setup (Ubuntu / Mac / WSL2)

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
cd YOUR_REPO_NAME
```

### 2. Install Python dependencies

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
```

Open `.env` and replace `your_api_key_here` with your actual Gemini key.

Or set it temporarily in terminal:

```bash
export GEMINI_API_KEY="your_key_here"
```

### 5. Run the agent

```bash
python3 agent.py
```

You'll be prompted to type a task. The agent opens a browser window and handles it.

---

## Example tasks

- `Go to reddit.com and find the top post in r/Python today`
- `Search Google for the latest iPhone price in Australia`
- `Go to wikipedia.org and summarise the article on black holes`
- `Check the weather in Melbourne on bom.gov.au`

---

## Windows (Command Prompt)

```
pip install -r requirements.txt
playwright install chromium --with-deps
copy .env.example .env
python agent.py
```

---

## Notes

- Your `.env` file is gitignored — your API key will NOT be committed.
- The agent uses `gemini-2.0-flash` by default. Change the model name in `agent.py` if needed.
- For headless/server use, set `headless=True` in the `Agent()` call inside `agent.py`.
