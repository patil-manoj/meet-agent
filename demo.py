import asyncio
import os
from datetime import datetime
from asr.transcription import Transcriber
from nlu.agents import SummarizerAgent, TaskAgent
from integrations.notion_client import NotionClient
from ingestion.meeting_connector import MeetingConnector

async def demo_meeting_processing():
    """
    Demonstrate the complete flow of meeting processing
    """
    print("\n=== Hybrid Meeting Agent Demo ===\n")

    # 1. Simulate meeting recording (using a sample transcript for demo)
    print("🎥 Simulating meeting recording...")
    sample_transcript = """
    Meeting Start - Project Planning Discussion
    
    John: Let's discuss the upcoming project milestones.
    
    Sarah: I'll take care of the frontend implementation. I think we can complete it by next Friday.
    
    Michael: Great, I'll handle the API integration. We should coordinate with the backend team.
    
    John: Perfect. Sarah, please create a design document by Wednesday.
    And Michael, can you set up the development environment by tomorrow?
    
    Sarah: Sure, I'll also need to coordinate with the UX team.
    
    Meeting End
    """

    # 2. Process the meeting content
    print("\n🎯 Processing meeting content...")
    
    # Initialize agents
    summarizer = SummarizerAgent()
    task_agent = TaskAgent()
    notion = NotionClient()

    # Generate summary
    print("\n📝 Generating meeting summary...")
    summary = await summarizer.generate_summary(sample_transcript)
    print("\nSummary:")
    print(summary)

    # Extract tasks
    print("\n📋 Extracting tasks...")
    tasks = await task_agent.extract_tasks(sample_transcript)
    print("\nTasks Identified:")
    for task in tasks:
        print(f"- {task.title} (Assigned to: {task.assignee}, Due: {task.due_date})")

    # 3. Create Notion page (if configured)
    try:
        print("\n📘 Creating Notion page...")
        meeting_id = f"DEMO-{datetime.now().strftime('%Y%m%d-%H%M')}"
        page_id = await notion.create_meeting_page(meeting_id, summary, tasks)
        print(f"✅ Notion page created successfully!")
    except Exception as e:
        print(f"⚠️  Notion integration skipped: {str(e)}")

    print("\n=== Demo Complete ===")

if __name__ == "__main__":
    asyncio.run(demo_meeting_processing())