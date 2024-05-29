# Test Plan Creator Bot for Slack

## Description

The Test Plan Creator Bot is a Slack application designed to assist software developers and QA teams in generating comprehensive test plans. By interacting with this bot directly within Slack, users can quickly create detailed test cases, which are then neatly organized in a Google Sheet. The bot leverages the power of OpenAI's language model, Claude, to intelligently generate test cases based on the provided feature information.

## Features

- Accepts feature names and details directly within Slack.
- Interactive prompts to gather additional information such as acceptance criteria and API details.
- Utilizes machine learning to generate a wide range of test cases.
- Organizes generated test cases into a Google Sheet template.
- Streamlines the test plan creation process, saving time and ensuring thorough coverage.

## Installation

To use the Test Plan Creator Bot, you'll need to set up several services, including Slack, AWS, and Google Sheets. Below you'll find steps to get started:

### Prerequisites

- A Slack account with permissions to create apps
- AWS account with access to Bedrock AI services
- Google Cloud account with the Google Sheets API enabled

### Clone the Repository

First, clone the repository to your local machine:

```sh
git clone https://github.com/your-username/test-plan-creator.git
cd test-plan-creator
```

### Install Dependencies

Install the required Python libraries:

```sh
pip install -r requirements.txt
```

## Usage

To start the Flask application, run:

```sh
flask run
```

Then, go to your Slack workspace where the bot has been installed to begin interacting with the bot. Simply send the message "Hi" to start the test plan creation process.

## Security

Test Plan Creator Bot implements several security measures:

- All sensitive information such as tokens and credentials are encrypted using Fernet before storage and decrypted at runtime.
- Requests from Slack are verified against a signature to authenticate the source.
- AWS IAM roles are used with limited permissions, which are assumed at runtime as needed.
