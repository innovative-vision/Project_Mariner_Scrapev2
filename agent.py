import asyncio
import os
from dotenv import load_dotenv
from browser_use import Agent
from browser_use.browser.browser import Browser, BrowserConfig
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    raise ValueError("OPENROUTER_API_KEY not set. Add it to your .env file.")

llm = ChatOpenAI(
    model="google/gemini-2.5-flash",
    openai_api_key=api_key,
    openai_api_base="https://openrouter.ai/api/v1",
    temperature=0.0,
)

browser = Browser(
    config=BrowserConfig(
        headless=True,
    )
)

async def run_task(task: str):
    agent = Agent(
        task=task,
        llm=llm,
        browser=browser,
    )
    result = await agent.run()
    print("\n--- RESULT ---")
    print(result)
    return result

if __name__ == "__main__":
    print("Browser-Use Agent — Gemini Edition (via OpenRouter)")
    print("Type your task below. The agent will browse the web and complete it.")
    print("Example: 'Go to reddit.com and find the top post in r/Python today'\n")

    task = input("Task: ").strip()
    if not task:
        task = "Go to google.com and tell me what the weather is in Melbourne, Australia"

    asyncio.run(run_task(task))
