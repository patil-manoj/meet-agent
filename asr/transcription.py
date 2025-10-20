import whisper
from typing import Optional

class Transcriber:
    def __init__(self):
        self.model = whisper.load_model("base")

    async def transcribe(self, audio_url: str) -> str:
        """
        Transcribe audio from URL using Whisper
        """
        try:
            # For demo, assuming local file. In production, download from URL first
            result = self.model.transcribe(audio_url)
            return result["text"]
        except Exception as e:
            raise Exception(f"Transcription failed: {str(e)}")