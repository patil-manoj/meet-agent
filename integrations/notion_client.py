from notion_client import Client
from typing import List, Dict
import os
from dotenv import load_dotenv

load_dotenv()

class NotionClient:
    def __init__(self):
        self.client = Client(auth=os.getenv("NOTION_TOKEN"))
        self.database_id = os.getenv("NOTION_DATABASE_ID")

    async def create_meeting_page(self, meeting_id: str, summary: str, tasks: List[Dict]) -> str:
        """
        Create a Notion page for the meeting with summary and tasks
        """
        try:
            page = self.client.pages.create(
                parent={"database_id": self.database_id},
                properties={
                    "Meeting ID": {"title": [{"text": {"content": meeting_id}}]},
                    "Status": {"select": {"name": "Completed"}},
                },
                children=[
                    {
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [{"type": "text", "text": {"content": "Summary"}}]
                        }
                    },
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": summary}}]
                        }
                    },
                    {
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [{"type": "text", "text": {"content": "Tasks"}}]
                        }
                    },
                    *[self._create_task_block(task) for task in tasks]
                ]
            )
            return page.id
        except Exception as e:
            raise Exception(f"Failed to create Notion page: {str(e)}")

    def _create_task_block(self, task: Dict) -> Dict:
        """
        Create a task block for Notion
        """
        return {
            "object": "block",
            "type": "to_do",
            "to_do": {
                "rich_text": [{"type": "text", "text": {"content": f"{task['title']} - Assigned to: {task['assignee']} (Due: {task['due_date']})"}}],
                "checked": False
            }
        }