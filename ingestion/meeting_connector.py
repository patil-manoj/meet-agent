from abc import ABC, abstractmethod
from typing import Optional, Dict, List
import aiohttp
import os
from datetime import datetime, timedelta
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import msal
import jwt
import time
from dotenv import load_dotenv

load_dotenv()

class MeetingPlatform(ABC):
    @abstractmethod
    async def get_recording_url(self, meeting_id: str) -> str:
        pass

    @abstractmethod
    async def get_meeting_metadata(self, meeting_id: str) -> Dict:
        pass
    
    @abstractmethod
    async def get_transcript(self, meeting_id: str) -> str:
        pass

class ZoomConnector(MeetingPlatform):
    def __init__(self):
        self.client_id = os.getenv("ZOOM_CLIENT_ID")
        self.client_secret = os.getenv("ZOOM_CLIENT_SECRET")
        self.account_id = os.getenv("ZOOM_ACCOUNT_ID")
        self.base_url = "https://api.zoom.us/v2"
        self._access_token = None
        self._token_expiry = None

    async def _get_access_token(self):
        if self._access_token and self._token_expiry and datetime.now() < self._token_expiry:
            return self._access_token

        print("Attempting to get Zoom access token...")
        print(f"Account ID: {self.account_id}")
        print(f"Client ID: {self.client_id}")
        
        async with aiohttp.ClientSession() as session:
            auth_url = "https://zoom.us/oauth/token"
            auth_string = self._get_base64_auth()
            print(f"Base64 Auth String: {auth_string}")
            
            auth_headers = {
                "Authorization": f"Basic {auth_string}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            data = {
                "grant_type": "account_credentials",
                "account_id": self.account_id
            }

            try:
                async with session.post(auth_url, headers=auth_headers, data=data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Failed to get access token. Status: {response.status}, Response: {error_text}")
                    
                    token_data = await response.json()
                    if "access_token" not in token_data:
                        raise Exception(f"Invalid token response: {token_data}")
                        
                    self._access_token = token_data["access_token"]
                    self._token_expiry = datetime.now() + timedelta(seconds=int(token_data["expires_in"]) - 300)
                    return self._access_token
            except Exception as e:
                raise Exception(f"Error getting access token: {str(e)}")

    def _get_base64_auth(self) -> str:
        """Generate Base64 encoded authentication string"""
        import base64
        # Remove any whitespace from credentials
        client_id = self.client_id.strip()
        client_secret = self.client_secret.strip()
        auth_string = f"{client_id}:{client_secret}"
        return base64.b64encode(auth_string.encode()).decode('utf-8')

    async def get_recording_url(self, meeting_id: str) -> str:
        token = await self._get_access_token()
        async with aiohttp.ClientSession() as session:
            # First, verify the meeting exists
            meeting_url = f"{self.base_url}/meetings/{meeting_id}"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            print(f"Checking meeting {meeting_id}...")
            async with session.get(meeting_url, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    print(f"Error getting meeting: Status {response.status}, Response: {error_text}")
                    raise Exception(f"Meeting not found or not accessible: {error_text}")
                meeting_data = await response.json()
                print(f"Meeting found: {meeting_data.get('topic', 'No topic')}")

            # Then get the recordings
            recordings_url = f"{self.base_url}/meetings/{meeting_id}/recordings"
            print(f"Fetching recordings...")
            async with session.get(recordings_url, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    print(f"Error getting recordings: Status {response.status}, Response: {error_text}")
                    raise Exception(f"Failed to get recordings: {error_text}")
                
                data = await response.json()
                print(f"Recording data: {data}")
                
                if "recording_files" in data and data["recording_files"]:
                    # Get the audio-only or shared screen recording
                    for recording in data["recording_files"]:
                        if recording["recording_type"] in ["audio_only", "shared_screen_with_speaker_view"]:
                            print(f"Found recording: {recording['recording_type']}")
                            return recording["download_url"]
                    print("No suitable recording type found")
                else:
                    print("No recordings found for this meeting")
                return None

    async def get_transcript(self, meeting_id: str) -> str:
        token = await self._get_access_token()
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/meetings/{meeting_id}/recordings/transcripts"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            async with session.get(url, headers=headers) as response:
                data = await response.json()
                if "recording_transcripts" in data:
                    # Get the VTT transcript URL and download it
                    transcript_url = data["recording_transcripts"][0]["download_url"]
                    async with session.get(transcript_url, headers=headers) as transcript_response:
                        return await transcript_response.text()
                return None

    async def get_meeting_metadata(self, meeting_id: str) -> Dict:
        token = await self._get_access_token()
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/meetings/{meeting_id}"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            async with session.get(url, headers=headers) as response:
                data = await response.json()
                return {
                    "platform": "zoom",
                    "id": meeting_id,
                    "topic": data.get("topic"),
                    "start_time": data.get("start_time"),
                    "duration": data.get("duration"),
                    "participants": data.get("participants_count", 0)
                }

class TeamsConnector(MeetingPlatform):
    def __init__(self):
        self.client_id = os.getenv("TEAMS_CLIENT_ID")
        self.client_secret = os.getenv("TEAMS_CLIENT_SECRET")
        self.tenant_id = os.getenv("TEAMS_TENANT_ID")
        self.base_url = "https://graph.microsoft.com/v1.0"
        self._access_token = None
        self._token_expiry = None

    async def _get_access_token(self):
        if self._access_token and self._token_expiry and datetime.now() < self._token_expiry:
            return self._access_token

        app = msal.ConfidentialClientApplication(
            self.client_id,
            authority=f"https://login.microsoftonline.com/{self.tenant_id}",
            client_credential=self.client_secret
        )

        result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
        if "access_token" in result:
            self._access_token = result["access_token"]
            self._token_expiry = datetime.now() + timedelta(seconds=3600)
            return self._access_token
        else:
            raise Exception(f"Failed to get Teams access token: {result.get('error_description')}")

    async def get_recording_url(self, meeting_id: str) -> str:
        token = await self._get_access_token()
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/users/meetings/{meeting_id}/recordings"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            async with session.get(url, headers=headers) as response:
                data = await response.json()
                if "value" in data and len(data["value"]) > 0:
                    return data["value"][0]["accessUrl"]
                return None

    async def get_transcript(self, meeting_id: str) -> str:
        token = await self._get_access_token()
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/users/meetings/{meeting_id}/transcripts"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            async with session.get(url, headers=headers) as response:
                data = await response.json()
                if "value" in data and len(data["value"]) > 0:
                    transcript_url = data["value"][0]["downloadUrl"]
                    async with session.get(transcript_url, headers=headers) as transcript_response:
                        return await transcript_response.text()
                return None

    async def get_meeting_metadata(self, meeting_id: str) -> Dict:
        token = await self._get_access_token()
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/users/meetings/{meeting_id}"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            async with session.get(url, headers=headers) as response:
                data = await response.json()
                return {
                    "platform": "teams",
                    "id": meeting_id,
                    "subject": data.get("subject"),
                    "start_time": data.get("startDateTime"),
                    "end_time": data.get("endDateTime"),
                    "participants": len(data.get("participants", []))
                }

class GoogleMeetConnector(MeetingPlatform):
    def __init__(self):
        self.credentials_path = os.getenv("GOOGLE_MEET_CREDENTIALS")
        self.token_path = os.getenv("GOOGLE_MEET_TOKEN")
        self.scopes = [
            'https://www.googleapis.com/auth/drive.readonly',
            'https://www.googleapis.com/auth/calendar.readonly'
        ]
        self._creds = None

    def _get_credentials(self):
        if self._creds and self._creds.valid:
            return self._creds

        if os.path.exists(self.token_path):
            self._creds = Credentials.from_authorized_user_file(self.token_path, self.scopes)

        if not self._creds or not self._creds.valid:
            if self._creds and self._creds.expired and self._creds.refresh_token:
                self._creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, self.scopes)
                self._creds = flow.run_local_server(port=0)
                with open(self.token_path, 'w') as token:
                    token.write(self._creds.to_json())

        return self._creds

    async def get_recording_url(self, meeting_id: str) -> str:
        creds = self._get_credentials()
        service = build('drive', 'v3', credentials=creds)
        
        # Search for the recording in Google Drive
        query = f"name contains '{meeting_id}' and mimeType contains 'video/'"
        results = service.files().list(q=query, spaces='drive').execute()
        files = results.get('files', [])
        
        if files:
            return f"https://drive.google.com/file/d/{files[0]['id']}/view"
        return None

    async def get_transcript(self, meeting_id: str) -> str:
        creds = self._get_credentials()
        service = build('drive', 'v3', credentials=creds)
        
        # Search for the transcript file
        query = f"name contains '{meeting_id}' and mimeType contains 'text/'"
        results = service.files().list(q=query, spaces='drive').execute()
        files = results.get('files', [])
        
        if files:
            request = service.files().get_media(fileId=files[0]['id'])
            return request.execute().decode('utf-8')
        return None

    async def get_meeting_metadata(self, meeting_id: str) -> Dict:
        creds = self._get_credentials()
        service = build('calendar', 'v3', credentials=creds)
        
        event = service.events().get(calendarId='primary', eventId=meeting_id).execute()
        return {
            "platform": "google_meet",
            "id": meeting_id,
            "title": event.get('summary'),
            "start_time": event.get('start', {}).get('dateTime'),
            "end_time": event.get('end', {}).get('dateTime'),
            "participants": len(event.get('attendees', []))
        }

class MeetingConnector:
    def __init__(self):
        self.platforms = {
            "zoom": ZoomConnector(),
            "teams": TeamsConnector(),
            "google_meet": GoogleMeetConnector()
        }

    async def get_recording(self, meeting_id: str, platform: str) -> Optional[str]:
        """Get recording URL from specified platform"""
        if platform not in self.platforms:
            raise ValueError(f"Unsupported platform: {platform}")
        
        connector = self.platforms[platform]
        return await connector.get_recording_url(meeting_id)

    async def get_metadata(self, meeting_id: str, platform: str) -> Dict:
        """Get meeting metadata from specified platform"""
        if platform not in self.platforms:
            raise ValueError(f"Unsupported platform: {platform}")
        
        connector = self.platforms[platform]
        return await connector.get_meeting_metadata(meeting_id)

    async def get_transcript(self, meeting_id: str, platform: str) -> Optional[str]:
        """Get meeting transcript from specified platform"""
        if platform not in self.platforms:
            raise ValueError(f"Unsupported platform: {platform}")
        
        connector = self.platforms[platform]
        return await connector.get_transcript(meeting_id)