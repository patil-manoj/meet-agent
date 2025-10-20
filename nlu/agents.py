import google.generativeai as genai
from typing import List, Dict
from pydantic import BaseModel, Field
import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

class Task(BaseModel):
    title: str = Field(description="The title of the task")
    assignee: str = Field(description="The person assigned to the task")
    due_date: str = Field(description="The due date for the task")
    description: str = Field(description="Detailed description of the task")

class SummarizerAgent:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-pro-latest')

    async def generate_summary(self, transcript: str) -> str:
        prompt = """You are a professional meeting summarizer. Create a concise summary with key points from the following transcript:

        Transcript:
        {transcript}
        
        Please provide a clear and structured summary."""
        
        response = await asyncio.to_thread(
            self.model.generate_content,
            prompt.format(transcript=transcript)
        )
        return response.text

class TaskAgent:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-pro-latest')

    async def extract_tasks(self, transcript: str) -> List[Task]:
        prompt = """Extract actionable tasks from the meeting transcript and format them as a JSON array.

        Here is the transcript:
        {transcript}

        Format your response as a JSON array of tasks, where each task has these fields:
        - title (string): A clear task title
        - assignee (string): The person assigned to the task
        - due_date (string): The due date in YYYY-MM-DD format
        - description (string): A detailed description of what needs to be done

        Example output:
        [
          {{
            "title": "Create Design Document",
            "assignee": "Sarah",
            "due_date": "2025-10-23",
            "description": "Create comprehensive design documentation for the project"
          }}
        ]

        Return only the JSON array, no additional text or markdown formatting."""

        response = await asyncio.to_thread(
            self.model.generate_content,
            prompt.format(transcript=transcript)
        )
        
        # Parse the response into Task objects
        import json
        try:
            # Remove any leading/trailing non-JSON content
            text = response.text.strip()
            if text.startswith('```json'):
                text = text[7:]
            if text.startswith('```'):
                text = text[3:]
            if text.endswith('```'):
                text = text[:-3]
            text = text.strip()
            
            tasks_data = json.loads(text)
            if not isinstance(tasks_data, list):
                tasks_data = [tasks_data]
            
            return [Task(**task) for task in tasks_data]
        except Exception as e:
            print(f"Error parsing tasks: {str(e)}")
            print(f"Raw response: {response.text}")
            return []

class IntegratorAgent:
    async def dispatch_tasks(self, tasks: List[Task]) -> None:
        """
        Dispatch tasks to various integration endpoints (Notion, etc.)
        """
        # Implementation for task dispatch logic
        pass