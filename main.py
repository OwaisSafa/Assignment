import requests
import logging
import time
import threading
from typing import List, Optional, Dict

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Suno:
    CLERK_BASE_URL = "https://clerk.suno.com"
    BASE_URL = "https://studio-api.suno.ai"
    API_VERSION = "5.26.3"

    def __init__(self, phone_number: str):
        self.phone_number = phone_number.strip()
        self.client = requests.Session()  # Use session to persist connections
        self.sid = None
        self.current_token = None
        self.authorization_token = None
        self.sign_in()

    def sign_in(self):
        """Authenticate user by phone number and OTP."""
        url = f"{self.CLERK_BASE_URL}/v1/client/sign_ins?_clerk_js_version={self.API_VERSION}"
        data = {"identifier": self.phone_number}
        response = self._post(url, data=data)

        if response:
            sign_in_attempt = response.get('response')
            self.authorization_token = response.headers.get('Authorization')
            logger.info("Sign-in attempt successful.")
            self.request_otp(sign_in_attempt)
        else:
            raise Exception(f"Sign-in failed for {self.phone_number}")

    def request_otp(self, sign_in_attempt: Dict):
        """Send OTP to the user's phone."""
        phone_number_id = sign_in_attempt.get('supported_first_factors', [{}])[0].get('phone_number_id')
        sign_in_attempt_id = sign_in_attempt.get('id')

        if not phone_number_id or not sign_in_attempt_id:
            raise Exception("Failed to retrieve required OTP details from the sign-in attempt.")

        url = f"{self.CLERK_BASE_URL}/v1/client/sign_ins/{sign_in_attempt_id}/prepare_first_factor?_clerk_js_version={self.API_VERSION}"
        data = {"phone_number_id": phone_number_id, "strategy": "phone_code"}
        response = self._post(url, data=data)

        if response:
            logger.info(f"OTP sent to {self.phone_number}.")
            otp_code = input(f"🔑 Enter the OTP you received for {self.phone_number}: ")
            self.submit_otp(sign_in_attempt_id, otp_code)
        else:
            raise Exception("Failed to send OTP")

    def submit_otp(self, sign_in_attempt_id: str, otp_code: str):
        """Verify the OTP and establish a session."""
        url = f"{self.CLERK_BASE_URL}/v1/client/sign_ins/{sign_in_attempt_id}/attempt_first_factor?_clerk_js_version={self.API_VERSION}"
        data = {"strategy": "phone_code", "code": otp_code}
        response = self._post(url, data=data)

        if response:
            self.current_token = response['response'].get('last_active_session_id')
            self.sid = response['response'].get('created_session_id')
            if self.sid:
                logger.info("Session established successfully.")
                self._keep_alive()
            else:
                raise Exception("Failed to establish a session.")
        else:
            raise Exception("OTP verification failed")

    def generate_song(self, prompt: str, is_custom: bool = False) -> Optional[List[str]]:
        """Generate a song based on a prompt."""
        url = f"{self.BASE_URL}/api/generate/v2/"
        payload = {
            "make_instrumental": False,
            "mv": "chirp-v3-5",
            "prompt": prompt if is_custom else "",
            "gpt_description_prompt": prompt if not is_custom else "",
        }
        response = self._post(url, json=payload)

        if response:
            song_ids = [clip['id'] for clip in response['clips']]
            logger.info(f"Generated song IDs: {song_ids}")
            return song_ids
        return None

    def check_song_status(self, song_ids: List[str]) -> bool:
        """Check the readiness of the generated songs."""
        url = f"{self.BASE_URL}/api/feed/?ids={','.join(song_ids)}"
        response = self._get(url)

        if response:
            clips = response
            for clip in clips:
                logger.info(f"Song ID: {clip['id']}, Status: {clip['status']}")
            return all(clip['status'] in ['streaming', 'complete'] for clip in clips)
        return False

    def download_song(self, song_id: str) -> str:
        """Download the song using its ID."""
        url = f"{self.BASE_URL}/api/feed/?ids={song_id}"
        response = self._get(url)

        if response:
            audio_url = response[0].get('audio_url')
            if audio_url:
                return self._download_audio(audio_url, song_id)
            raise Exception("No audio URL found.")
        raise Exception("Failed to retrieve song details.")

    def _keep_alive(self):
        """Renew the authentication token to keep the session active."""
        if not self.sid:
            raise Exception("Session ID is not set. Cannot renew token.")

        url = f"{self.CLERK_BASE_URL}/v1/client/sessions/{self.sid}/tokens?_clerk_js_version={self.API_VERSION}"
        response = self._post(url)

        if response:
            self.current_token = response.get('jwt')
            self.client.headers.update({'Authorization': f"Bearer {self.current_token}"})
            logger.info("Session token renewed.")
        else:
            raise Exception("Failed to renew session token.")

    def _download_audio(self, audio_url: str, song_id: str) -> str:
        """Download the audio file."""
        filename = f"SunoMusic-{song_id}.mp3"
        with self.client.get(audio_url, stream=True) as r:
            r.raise_for_status()
            with open(filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        logger.info(f"Downloaded song: {filename}")
        return filename

    def _get(self, url: str) -> Optional[Dict]:
        """Perform a GET request and handle errors."""
        try:
            response = self.client.get(url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"GET request failed: {e}")
            return None

    def _post(self, url: str, data=None, json=None) -> Optional[Dict]:
        """Perform a POST request and handle errors."""
        try:
            response = self.client.post(url, data=data, json=json)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"POST request failed: {e}")
            return None


def main():
    print("Welcome to the Suno Music Generator!")
    phone_numbers = input("Enter phone numbers (comma-separated, including country code): ").split(",")
    unique_numbers = set(phone.strip() for phone in phone_numbers)

    sessions = []
    for phone in unique_numbers:
        try:
            sessions.append(Suno(phone))
        except Exception as e:
            logger.error(f"Failed to initialize session for {phone}: {e}")

    if not sessions:
        logger.error("No valid sessions available.")
        return

    prompt = input("Enter a creative prompt for the song: ")

    song_ids = None
    for session in sessions:
        try:
            logger.info(f"Generating song for {session.phone_number}...")
            song_ids = session.generate_song(prompt)
            if song_ids:
                break
        except Exception as e:
            logger.error(f"Error during song generation: {e}")

    if not song_ids:
        logger.error("Failed to generate song with all sessions.")
        return

    logger.info("Checking song readiness...")
    while not all(session.check_song_status(song_ids) for session in sessions):
        time.sleep(5)
        logger.info("Still waiting for songs to be ready...")

    logger.info("All songs are ready! Downloading...")
    for session in sessions:
        for song_id in song_ids:
            try:
                session.download_song(song_id)
            except Exception as e:
                logger.error(f"Failed to download song {song_id}: {e}")

if __name__ == "__main__":
    main()
