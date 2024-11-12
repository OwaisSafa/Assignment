# Suno Music Generator

This project automates the process of generating and downloading songs based on user-provided prompts through the Suno API. It integrates phone number authentication, OTP verification, and session management to ensure smooth operation over multiple attempts.

## Features

- **Phone number authentication**: Allows users to authenticate using their phone numbers.
- **OTP verification**: Sends and verifies the OTP to ensure secure login.
- **Song generation**: Creates a song using a provided prompt via Suno's API.
- **Session management**: Handles user sessions and token renewals to keep the session active.
- **Song status checking**: Monitors the status of generated songs.
- **Audio download**: Downloads the generated song in MP3 format once it's ready.

## Prerequisites

- Python 3.x
- `requests` library

You can install the required dependencies by running:

```bash
pip install requests
```

## Setup

1. Clone the repository:

```bash
git clone https://github.com/OwaisSafa/suno-music-generator.git
cd suno-music-generator
```

2. Edit the script to provide your phone number(s) and the prompt for song generation when prompted.

## Usage

1. Run the script:

```bash
python suno_music_generator.py
```

2. Enter your phone number(s) when prompted (include the country code). For example:
   ```
   +1234567890,+0987654321
   ```

3. Enter a creative prompt for the song when asked. The script will attempt to generate a song and download it when ready.

4. The script will handle OTP verification, session management, and the entire song generation process.

## How It Works

1. **Sign-In Process**: The script sends a phone number to Suno's Clerk service to initiate a sign-in attempt.
2. **OTP Request**: After receiving the sign-in attempt details, the script requests an OTP and prompts the user to input it.
3. **Session Establishment**: Once the OTP is verified, the session is established, and the script proceeds to generate the song.
4. **Song Generation**: The script sends a prompt to Suno’s API and retrieves the song IDs.
5. **Song Status Checking**: The script periodically checks the status of the generated songs until they are ready.
6. **Download**: Once the songs are ready, they are downloaded as MP3 files.

## Troubleshooting

- **Insufficient credits**: If you encounter an error related to insufficient credits, ensure your account has enough credits to generate songs.
- **Authentication Issues**: Double-check the phone numbers entered and make sure the OTP is entered correctly.

## License

This project is licensed under the MIT License.
