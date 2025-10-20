from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path

# Create templates directory
templates = Jinja2Templates(directory="ui/templates")

router = APIRouter()

@router.get("/")
async def dashboard(request: Request):
    """Render the main dashboard"""
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "title": "Meeting Assistant Dashboard"}
    )

@router.get("/meetings")
async def list_meetings(request: Request):
    """List all meetings"""
    # Demo meeting (in production, these would come from the database)
    meetings = [
        {
            "title": "Project Planning Discussion",
            "date": "October 19, 2025",
            "duration": "30 minutes",
            "status": "Completed",
            "summary": """
                <h3><strong>Key Outcomes:</strong></h3>
                <ul class="list-disc pl-5 space-y-2">
                    <li>Team established initial roles and responsibilities</li>
                    <li>Frontend development assigned to Sarah</li>
                    <li>API integration assigned to Michael</li>
                    <li>Coordination planned between frontend, backend, and UX teams</li>
                </ul>
            """,
            "tasks": [
                {
                    "title": "Complete Frontend Implementation",
                    "assignee": "Sarah",
                    "due_date": "2024-10-25"
                },
                {
                    "title": "Create Design Document",
                    "assignee": "Sarah",
                    "due_date": "2024-10-16"
                },
                {
                    "title": "Set Up Development Environment",
                    "assignee": "Michael",
                    "due_date": "2024-10-15"
                }
            ]
        }
    ]
    return templates.TemplateResponse(
        "meetings.html",
        {"request": request, "meetings": meetings}
    )

@router.get("/tasks")
async def list_tasks(request: Request):
    """List all tasks"""
    # Demo tasks (in production, these would come from the database)
    tasks = [
        {
            "title": "Complete Frontend Implementation",
            "assignee": "Sarah",
            "due_date": "2024-10-25",
            "description": "Implement the frontend components and integrate with the backend API",
            "completed": False
        },
        {
            "title": "Create Design Document",
            "assignee": "Sarah",
            "due_date": "2024-10-16",
            "description": "Create a comprehensive design document for the project including UX considerations",
            "completed": False
        },
        {
            "title": "Set Up Development Environment",
            "assignee": "Michael",
            "due_date": "2024-10-15",
            "description": "Configure and set up the development environment for the team",
            "completed": False
        }
    ]
    return templates.TemplateResponse(
        "tasks.html",
        {"request": request, "tasks": tasks}
    )