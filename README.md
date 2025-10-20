# Hybrid Meeting Agent

An AI-powered meeting assistant that captures, transcribes, and processes meeting content to generate summaries and actionable tasks.

## Features

- 🎥 Live meeting audio capture and transcription
- 📝 AI-powered meeting summarization
- ✅ Automatic task extraction
- 📊 Integration with Notion for task management
- ⏰ Automated task reminders
- 🌐 Web dashboard for meeting and task management

## Tech Stack

- Python 3.12+
- FastAPI
- Google Gemini AI
- LangChain
- Notion API
- SQLite/PostgreSQL
- Whisper ASR

## Setup

1. Clone the repository:
```bash
git clone [repository-url]
cd hybrid-meeting-agent
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
- Copy `.env.example` to `.env`
- Add your API keys and configuration

5. Run the application:
```bash
uvicorn main:app --reload
```

## Project Structure

- `/asr` - Audio transcription services
- `/db` - Database models and configuration
- `/ingestion` - Meeting platform connectors
- `/integrations` - Third-party service integrations
- `/nlu` - Natural language understanding components
- `/scheduler` - Task scheduling and reminders
- `/ui` - Web interface and API routes

## Usage

1. Access the web dashboard at `http://localhost:8000`
2. Start a meeting recording or upload an existing transcript
3. View generated summaries and tasks
4. Manage tasks and track progress through the dashboard

## API Endpoints

- `POST /meeting/summary` - Process meeting audio/transcript
- `GET /meetings` - List all meetings
- `GET /tasks` - List all tasks

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

MIT License