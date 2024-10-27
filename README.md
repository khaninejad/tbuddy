# Tbuddy

**Tbuddy** is a Twitch bot application designed to monitor streams, watch stream, and analyze data to generate live insights and comments. This application uses OpenAI or other AI models to interpret data, providing real-time responses and feedback. Tbuddy is available in both Free and Premium versions, with different levels of access and functionality.

## Features

- **Stream Monitoring and Analysis**: watch stream and analyzes Twitch streams to generate comments and insights.
- **Real-time Response**: Uses OpenAI and other models to analyze data and create responses based on user-defined or custom assistants.
- **Free and Premium Modes**: Free users are limited to 30-minute sessions, while Premium users get unlimited access.
- **Cross-Platform Support**: Compatible with Windows, macOS, and Linux.

---

## Table of Contents

1. [Requirements](#requirements)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Usage](#usage)
5. [License and EULA](#license-and-eula)
6. [Contributing](#contributing)
7. [Support](#support)

---

## Requirements

- **Python 3.8+**
- **Poetry** (for dependency management)
- An **OpenAI API Key** (or other AI model API keys)
- Twitch **Username and Password** for each user account (stored locally)

## Installation

### Download the Latest Release

To download the latest release of Tbuddy, visit the [Releases page](https://github.com/khaninejad/tbuddy/releases) and download the appropriate package for your platform.

### Building from Source

To build Tbuddy from the source, follow these steps:

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/khaninejad/tbuddy.git
   cd tbuddy

2. **Install Dependencies using Poetry:**:
   ```bash
   poetry install

3. **Run the Application:**:
    Navigate to the src directory:
   ```bash
   poetry install
   cd src
   poetry run python gui.py


### Configuration

OpenAI API Key

To access the analysis features, you need an API key from OpenAI (or similar).

    Obtain an API key by creating an account with OpenAI.
    Save your API key locally as instructed by the app’s prompts.

Twitch Username and Password

Each user requires a Twitch username and password to authenticate. These credentials will be stored locally on your device for login purposes.

    Note: Tbuddy is not transmit password to cloud or any other service and store information locally


## Configuration

### OpenAI API Key

To access the analysis features, you need an API key from OpenAI (or similar). 

1. **Obtain an API Key**:
   - Create an account with [OpenAI](https://beta.openai.com/signup/).
   - Follow the instructions to generate your [API key](https://platform.openai.com/api-keys).

2. **Save Your API Key**:
   - Upon starting the application for the first time, Tbuddy will prompt you to enter your OpenAI API key.
   - The API key will be stored locally for use during sessions.

### Twitch Username and Password

Each user requires a Twitch username and password to authenticate. These credentials will be stored locally on your device for login purposes.

1. **Enter Credentials**:
   - When prompted, provide your Twitch username and password. 
   - Ensure that your credentials are correct to avoid login issues.

> **Note**: Tbuddy stores this information on your device. Make sure to secure your local storage to protect sensitive data.


## Usage

### Launch the Application

1. **Start Tbuddy**:
   - Navigate to the `src` directory:
     ```bash
     cd src
     ```
   - Run the following command to start the GUI:
     ```bash
     poetry run python gui.py
     ```

### Free vs. Premium Access

- **Free Users**: 
  - Limited to 30-minute sessions.
  - Can set up only one user profile.

- **Premium Users**:
  - Enjoy unlimited session time.
  - Can set up multiple user profiles.

### Application Features

- **Stream Monitoring**: Tbuddy watches stream of Twitch and analyzes them in real time.
- **Comment Generation**: Based on the analysis, Tbuddy can generate live comments and insights using AI models.
- **User-Friendly Interface**: The application provides a straightforward GUI for easy interaction and configuration.


## License and EULA

- **End-User License Agreement (EULA)**: By using Tbuddy, you agree to the terms outlined in the [EULA](./EULA.md) governing this software.
  
- **License**: The source code is provided under the terms specified in the [LICENSE.txt](./LICENSE.txt) file. Make sure to review the licensing terms to understand your rights and responsibilities.

---


## Support

If you encounter any issues or need assistance, please reach out via the following methods:

- **GitHub Issues**: Open an issue in the [GitHub issues section](https://github.com/khaninejad/tbuddy/issues) for bugs, feature requests, or general inquiries.
- **Email Support**: Contact us at **info@tbuddy.chat** or **https://tbuddy.chat/contact-us/**  for more direct assistance.

We appreciate your feedback and are here to help!
