import requests
import logging
import time
from typing import List

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Suno:
    CLERK_BASE_URL = "https://clerk.suno.com"
    BASE_URL = 'https://studio-api.suno.ai'  # URL for generating songs

    def __init__(self, phone_number: str):
        self.phone_number = phone_number.strip()
        self.client = requests.Session()
        self.sid = None
        self.current_token = None
        self.authorization_token = None
        self.sign_in()

    def sign_in(self):
        """Step 1: Sign-in Request (Phone Number)"""
        url = f"{Suno.CLERK_BASE_URL}/v1/client/sign_ins?_clerk_js_version=5.26.3"
        headers = self._get_default_headers()
        data = {"identifier": self.phone_number}
        
        response = self.client.post(url, headers=headers, data=data)
        if response.status_code == 200:
            sign_in_attempt = response.json().get('response')
            self.authorization_token = response.headers.get('Authorization')
            logger.info("Sign-in attempt successful.")
            self.request_otp(sign_in_attempt)
        else:
            logger.error(f"Sign-in attempt failed with status: {response.status_code}")

    def request_otp(self, sign_in_attempt):
        """Step 2: Request OTP (Phone code)"""
        supported_first_factors = sign_in_attempt.get('supported_first_factors', [])
        if not supported_first_factors:
            logger.error("No supported first factors found.")
            return
        
        phone_number_id = supported_first_factors[0].get('phone_number_id')
        sign_in_attempt_id = sign_in_attempt['id']
        url = f"{Suno.CLERK_BASE_URL}/v1/client/sign_ins/{sign_in_attempt_id}/prepare_first_factor?_clerk_js_version=5.26.3"
        headers = self._get_authorization_headers()
        data = {"phone_number_id": phone_number_id, "strategy": "phone_code"}

        response = self.client.post(url, headers=headers, data=data)
        if response.status_code == 200:
            logger.info(f"OTP Sent Successfully to {self.phone_number}")
            otp_code = input(f"🔑 Enter the OTP you received for {self.phone_number}: ")
            self.submit_otp(sign_in_attempt_id, otp_code)
        else:
            logger.error("Failed to request OTP")

    def submit_otp(self, sign_in_attempt_id: str, otp_code: str):
        """Step 3: Submit OTP for verification."""
        url = f"{Suno.CLERK_BASE_URL}/v1/client/sign_ins/{sign_in_attempt_id}/attempt_first_factor?_clerk_js_version=5.26.3"
        headers = self._get_authorization_headers()
        data = {"strategy": "phone_code", "code": otp_code}

        response = self.client.post(url, headers=headers, data=data)
        if response.status_code == 200:
            logger.info("OTP Verification Successful")
            response_json = response.json()
            self.current_token = response_json['response'].get('last_active_session_id')  
            self.sid = response_json['response'].get('created_session_id')
            if self.sid:
                logger.info("Session established successfully.")
                self._keep_alive()
            else:
                logger.error("Session ID is not available in the response.")
                raise Exception("Session ID is not set. Cannot renew token.")
        else:
            logger.error("Failed to verify OTP")
            raise Exception("Failed to verify OTP")

    def _keep_alive(self) -> None:
        """Renew the authentication token periodically to keep the session active."""
        if not self.sid:
            logger.error("Session ID is not set. Cannot renew token.")
            raise Exception("Session ID is not set. Cannot renew token.")

        renew_url = f"{Suno.CLERK_BASE_URL}/v1/client/sessions/{self.sid}/tokens?_clerk_js_version=4.72.0-snapshot.vc141245"
        renew_response = self.client.post(renew_url)
        logger.info("Renew Token ♻️")

        if renew_response.status_code == 200:
            self.current_token = renew_response.json().get('jwt')
            self.client.headers['Authorization'] = f"Bearer {self.current_token}"
        else:
            logger.error("Failed to renew token.")
            raise Exception(f"Token renewal failed with status: {renew_response.status_code}")

    def generate_song(self, prompt: str, is_custom: bool = False) -> List[str]:
        """Generate a song based on a prompt."""
        url = f"{self.BASE_URL}/api/generate/v2/"
        payload = {
            "make_instrumental": False,
            "mv": "chirp-v3-5",
            "prompt": prompt if is_custom else "",
            "gpt_description_prompt": prompt if not is_custom else "",
        }

        response = self.client.post(url, json=payload)
        if response.status_code == 200:
            song_ids = [clip['id'] for clip in response.json()['clips']]
            logger.info(f"Generated song IDs: {song_ids}")
            return song_ids
        else:
            self._handle_generation_error(response)
            return None

    def check_song_status(self, song_ids: List[str]) -> bool:
        """Check if the songs are ready."""
        url = f"{self.BASE_URL}/api/feed/?ids={','.join(song_ids)}"
        response = self.client.get(url)

        if response.status_code == 200:
            clips = response.json()
            for clip in clips:
                logger.info(f"Song ID: {clip['id']}, Status: {clip['status']}")
            return all(clip['status'] in ['streaming', 'complete'] for clip in clips)
        else:
            logger.error(f"Failed to check song status: {response.text}")
            return False

    def download_song(self, song_id: str) -> str:
        """Download the song using its ID."""
        url = f"{self.BASE_URL}/api/feed/?ids={song_id}"
        response = self.client.get(url)

        if response.status_code == 200:
            audio_url = response.json()[0].get('audio_url')
            if audio_url:
                return self._download_audio(audio_url, song_id)
            else:
                logger.error(f"No audio URL found for song ID {song_id}. Response: {response.text}")
                raise Exception("No audio URL found")
        else:
            logger.error(f"Failed to retrieve song details: {response.text}")
            raise Exception("Song download failed")

    def _download_audio(self, audio_url: str, song_id: str) -> str:
        """Download the audio from the given URL."""
        filename = f"SunoMusic-{song_id}.mp3"
        try:
            with requests.get(audio_url, stream=True) as r:
                r.raise_for_status()
                with open(filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            logger.info(f"Downloaded song: {filename}")
            return filename
        except Exception as e:
            logger.error(f"Failed to download song from {audio_url}. Error: {str(e)}")
            raise Exception("Song download failed")

    def _get_default_headers(self):
        """Return default headers for requests."""
        return {
            "content-type": "application/x-www-form-urlencoded",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
            "Origin": Suno.CLERK_BASE_URL,
            "Referer": Suno.CLERK_BASE_URL,
        }

    def _get_authorization_headers(self):
        """Return headers including authorization token."""
        headers = self._get_default_headers()
        headers["Authorization"] = self.authorization_token
        return headers

    def _handle_generation_error(self, response):
        """Handle errors during song generation."""
        error_message = response.json().get("detail", "")
        if "Insufficient credits" in error_message:
            logger.error("Insufficient credits to generate song for this session.")
        else:
            logger.error(f"Failed to generate song: {response.text}")
            raise Exception("Song generation failed")


def main():
    print("Welcome to the Suno Music Generator!")
    phone_numbers = input("Please enter your phone numbers (comma-separated, including country code): ").split(",")  
    suno_sessions = []

    # Create a session for each unique phone number
    unique_phone_numbers = set(phone.strip() for phone in phone_numbers)
    for phone_number in unique_phone_numbers:
        suno_sessions.append(Suno(phone_number))

    # Ask for the prompt only once
    prompt = input("Enter a creative prompt for the song: ")

    # Generate a song with each session until one succeeds or fails due to insufficient credits
    song_ids = None
    for suno in suno_sessions:
        try:
            # Log which phone number is being used to generate the song
            logger.info(f"Attempting to generate song using phone number: {suno.phone_number}")
            
            # Use the same prompt for all sessions
            song_ids = suno.generate_song(prompt)

            # If the song generation succeeds, proceed to check and download songs
            if song_ids:
                logger.info(f"🎶 Song generated successfully for {suno.phone_number}! 🎶")
                break  # Exit the loop if song generation is successful
            else:
                logger.error(f"Failed to generate song for {suno.phone_number}. Moving to next session.")
        except Exception as e:
            if "Insufficient credits" in str(e):
                logger.error(f"Insufficient credits for session {suno.phone_number}, trying next session...")
                continue  # Move to the next session if credits are insufficient
            else:
                logger.error(f"Unexpected error for session {suno.phone_number}: {str(e)}")
                break  # Exit loop if the error is not related to credits

    if not song_ids:
        logger.error("All sessions failed to generate songs. Exiting...")
        return

    # Check if all the songs are ready
    logger.info("\nChecking if the songs are ready for download...\n")
    
    while True:
        time.sleep(5)  # Wait before checking again
        if suno.check_song_status(song_ids):
            logger.info("🎶 All songs are ready for download! 🎶")
            break
        else:
            logger.info("⏳ Some songs are still not ready. Checking again...")

    # Download each song
    logger.info("\nStarting the download process...\n")
    for song_id in song_ids:
        try:
            suno._keep_alive()  # Renew the token before each download attempt
            filename = suno.download_song(song_id)
            logger.info(f"Successfully downloaded: {filename}")
        except Exception as e:
            logger.error(f"❌ Failed to download song with ID {song_id}. Error: {str(e)}")

if __name__ == "__main__":
    main()