from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import os

def initialize_slack_client(slack_bot_token):
    """
    Initializes and returns an instance of the Slack WebClient using the token in the environment.
    Raises:
        KeyError: If the SLACK_BOT_TOKEN is not found in the environment.
    Returns:
        WebClient: The Slack WebClient instance.
    """
    return WebClient(token=slack_bot_token)

def send_slack_message(slack_client, channel_id, text, thread_ts=None):
    try:
        message_data = {'channel': channel_id, 'text': text}
        if thread_ts:  # This checks if thread_ts is not None
            message_data['thread_ts'] = thread_ts
        response = slack_client.chat_postMessage(**message_data)
        return response.data['ts']
    except SlackApiError as e:
        print(f"Error sending message to Slack: {e.response['error']}")
        raise

def publish_app_home(user_id, slack_client):
    try:
        # Define the home view - A simple greeting message block
        home_view = {
            "type": "home",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": ":wave: *Hi, Welcome to Test Plan Creator!* :\n\n"
                                " :bob_the_builder: Let's build a test plan together for your new feature \n\n"
                                ":arrow_right: Navigate to Messages Tab and send 'Hi' to start creating a test plan."
                    }
                }
            ]
        }

        # Publish the view to the specified user's App Home
        response = slack_client.views_publish(user_id=user_id, view=home_view)
        return response
    except SlackApiError as e:
        print(f"Got an error: {e.response['error']} - {e.response['response_metadata']}")
        raise e        