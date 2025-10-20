import asyncio
from integrations.notion_client import NotionClient
from dotenv import load_dotenv
import os

async def test_notion_connection():
    print("\n=== Testing Notion Integration ===\n")
    
    # Initialize Notion client
    notion = NotionClient()
    
    try:
        # Test basic connection
        print("1. Testing Notion API connection...")
        client = notion.client
        
        # Create a test meeting page
        print("\n2. Creating a test meeting page...")
        meeting_id = "TEST-MEETING-001"
        summary = """
        Meeting Summary:
        - Discussed project timeline
        - Assigned tasks to team members
        - Set up next meeting date
        """
        
        tasks = [
            {
                "title": "Update project timeline",
                "assignee": "John",
                "due_date": "2025-10-20",
                "description": "Review and update the project timeline based on today's discussion"
            }
        ]
        
        page_id = await notion.create_meeting_page(meeting_id, summary, tasks)
        print(f"\n✅ Success! Created Notion page with ID: {page_id}")
        print(f"\nTo view the page, check your Notion workspace")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\nTroubleshooting tips:")
        print("1. Verify your NOTION_TOKEN is correct")
        print("2. Make sure you've shared the database with your integration")
        print("3. Verify the NOTION_DATABASE_ID is correct")
        print("4. Ensure your integration has write permissions")

if __name__ == "__main__":
    asyncio.run(test_notion_connection())