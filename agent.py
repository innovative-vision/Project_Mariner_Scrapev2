import asyncio
import os
from dotenv import load_dotenv
from browser_use import Agent
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not set. Add it to your .env file.")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=api_key,
    temperature=0.0,
)

async def run_task(task: str):
    agent = Agent(
        task=task,
        llm=llm,
    )
    result = await agent.run()
    print("\n--- RESULT ---")
    print(result)
    return result

if __name__ == "__main__":
    print("Browser-Use Agent — Gemini Edition")
    print("Type your task below. The agent will open a browser and complete it.")
    print("Example: 'Go to reddit.com and find the top post in r/Python today'\n")

    task = input("Task: ").strip()
    if not task:
        task = "Go to google.com and tell me what the weather is in Melbourne, Australia"

    asyncio.run(run_task(task))
