from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import uvicorn
from ui.routes import router as ui_router

from ingestion.meeting_connector import MeetingConnector
from asr.transcription import Transcriber
from nlu.agents import SummarizerAgent, TaskAgent, IntegratorAgent
from integrations.notion_client import NotionClient
from scheduler.meeting_scheduler import MeetingScheduler
from db.database import init_db

app = FastAPI(title="Hybrid Meeting Agent")

# Mount UI routes
app.include_router(ui_router)
app.mount("/static", StaticFiles(directory="ui/static"), name="static")

class MeetingInput(BaseModel):
    audio_url: Optional[str] = None
    transcript: Optional[str] = None
    meeting_id: str

@app.on_event("startup")
async def startup_event():
    await init_db()

@app.post("/meeting/summary")
async def process_meeting(meeting_input: MeetingInput):
    try:
        # Initialize components
        transcriber = Transcriber()
        summarizer = SummarizerAgent()
        task_agent = TaskAgent()
        integrator = IntegratorAgent()
        notion = NotionClient()
        
        # Get transcript (from audio or direct input)
        if meeting_input.audio_url:
            transcript = await transcriber.transcribe(meeting_input.audio_url)
        elif meeting_input.transcript:
            transcript = meeting_input.transcript
        else:
            raise HTTPException(status_code=400, detail="Either audio_url or transcript must be provided")
        
        # Process meeting content
        summary = await summarizer.generate_summary(transcript)
        tasks = await task_agent.extract_tasks(transcript)
        
        # Integrate with Notion
        await integrator.dispatch_tasks(tasks)
        await notion.create_meeting_page(meeting_input.meeting_id, summary, tasks)
        
        return {
            "meeting_id": meeting_input.meeting_id,
            "summary": summary,
            "tasks": tasks
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)