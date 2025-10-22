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
    meeting_id: str
    platform: str = "zoom"  # Default to zoom
    audio_url: Optional[str] = None
    transcript: Optional[str] = None

@app.on_event("startup")
async def startup_event():
    await init_db()

@app.post("/meeting/summary")
async def process_meeting(meeting_input: MeetingInput):
    try:
        print(f"\nProcessing meeting {meeting_input.meeting_id} from {meeting_input.platform}")
        
        # Initialize components
        meeting_connector = MeetingConnector()
        transcriber = Transcriber()
        summarizer = SummarizerAgent()
        task_agent = TaskAgent()
        integrator = IntegratorAgent()
        notion = NotionClient()
        
        # Get meeting content from platform
        try:
            print("Attempting to get transcript...")
            # First try to get direct transcript
            transcript = await meeting_connector.get_transcript(meeting_input.meeting_id, meeting_input.platform)
            if transcript:
                print("Got transcript directly from platform")
            
            # If no transcript, try getting recording and transcribe it
            if not transcript:
                print("No direct transcript, trying to get recording...")
                recording_url = await meeting_connector.get_recording(meeting_input.meeting_id, meeting_input.platform)
                if recording_url:
                    print(f"Got recording URL: {recording_url}")
                    transcript = await transcriber.transcribe(recording_url)
                    print("Successfully transcribed recording")
                else:
                    print("No recording found")
                
            # If still no transcript, fall back to provided input
            if not transcript:
                print("No platform content, checking provided input...")
                if meeting_input.audio_url:
                    print(f"Using provided audio URL: {meeting_input.audio_url}")
                    transcript = await transcriber.transcribe(meeting_input.audio_url)
                elif meeting_input.transcript:
                    print("Using provided transcript")
                    transcript = meeting_input.transcript
                else:
                    print("No content available")
                    raise HTTPException(status_code=400, detail="Could not retrieve meeting content and no transcript provided")
        
        except Exception as e:
            if meeting_input.audio_url:
                transcript = await transcriber.transcribe(meeting_input.audio_url)
            elif meeting_input.transcript:
                transcript = meeting_input.transcript
            else:
                raise HTTPException(status_code=400, detail=f"Failed to retrieve meeting content: {str(e)}")
        
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