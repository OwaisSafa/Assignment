# Suno Music Generator API Automation

## Overview
This project automates the process of logging in, generating music based on prompts, and downloading the generated songs using the Suno Music Generation API. It handles user authentication via OTP, generates custom songs from multiple sessions (with multiple phone numbers), and downloads the songs once they're ready.

## Features
- **Multi-Session Handling**: Supports multiple sessions using different phone numbers.
- **OTP Authentication**: Automates OTP-based authentication for each session.
- **Music Generation**: Automatically generates music based on user-provided prompts.
- **Song Status Check**: Continuously checks the status of song generation until the songs are ready for download.
- **Automatic Download**: Downloads songs when the generation process is complete.

## How It Works

1. **Session Handling**:
   - You can input multiple phone numbers (in a comma-separated format).
   - For each phone number, a session is created. The program handles OTP verification for each session, ensuring that all are logged in and authenticated.

2. **OTP Authentication**:
   - After entering a phone number, an OTP will be sent to the corresponding device.
   - You will manually enter the OTP for each session during the runtime. Once verified, the session is established and kept alive during the process.

3. **Music Generation**:
   - After authentication, the program prompts you to enter a creative prompt for song generation.
   - Using the Suno API, the song is generated, and its unique song IDs are returned.
   - The generated song(s) are checked periodically to see if they are ready for download.

4. **Downloading the Song**:
   - Once all songs are ready, they are automatically downloaded in `.mp3` format.
   - The files are named `SunoMusic-[song_id].mp3` and saved in the current directory.

## Multi-Session Flow

The program allows you to manage multiple sessions using different phone numbers. For each phone number:
1. A new **Suno session** is created.
2. **OTP authentication** is handled for that session.
3. The program continues generating songs for each session sequentially.
4. If one session fails (due to incorrect OTP or other issues), the program tries the next available session.

This is useful for scenarios where multiple accounts are used to generate multiple songs concurrently.

## Example Workflow
1. **Sign-in & OTP**:
   - The user enters their phone number(s).
   - For each phone number, an OTP is sent, which the user enters into the program.

2. **Song Generation**:
   - The user is prompted to enter a creative song prompt (e.g., "A relaxing lo-fi beat for studying").
   - The song generation request is sent to the API.
   - If a session has insufficient credits to generate the song, the program will automatically attempt to generate the song using the next available session, notifying the user of the transition.

3. **Checking Song Status**:
   - The program checks the status of the generated song every few seconds.
   - Once all songs are ready, they are downloaded.

4. **Download**:
   - The songs are downloaded as `.mp3` files.

## Logging
The project includes logging for key events such as:
- Successful or failed OTP authentication
- Song generation status
- Download status
- Errors during any step

This logging information is helpful for debugging and understanding the execution flow.

## Dependencies
- **requests**: Used for making HTTP requests to the Suno API.
- **logging**: Provides real-time logging of important steps in the process.

## Troubleshooting

1. **OTP Issues**: If you don’t receive the OTP, ensure your phone number is correct and includes the country code.
2. **Session Timeouts**: If a session expires, the program automatically renews the session token to keep the session alive.
3. **Song Generation Fails**: Check if you have sufficient credits in your Suno account to generate songs.

## Submission
This project is part of an assignment for automating API workflows. It demonstrates:
- Handling multiple sessions with OTP verification.
- Generating music using Suno's API.
- Downloading songs automatically once the generation is complete.
