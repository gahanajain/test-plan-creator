from flask import Flask, request, jsonify, abort
from slack_integration import send_slack_message, initialize_slack_client, publish_app_home
from bedrock_integration import invoke_claude, build_claude_prompt
from aws_session import assume_role
from sheets_manager import initialize_sheets_service, duplicate_template_sheet, update_sheet_with_data
from utils import verify_slack_signature
from parse_text import parse_feature_text, is_greeting, parse_claude_response
from encryption import decrypt_file
from datetime import date
from threading import Lock
import html
import json

# Initialize the Flask application
app = Flask(__name__)

# Lock for thread-safe operation on global state
state_lock = Lock()

# Global dictionary to maintain state (replace this with a persistent data store in production)
conversation_states = {}

# Load and decrypt the encrypted configuration file with Slack and Google credentials
config = decrypt_file('slack_google_credentials.enc')

# Initialize services with the decrypted configuration
slack_client = initialize_slack_client(config['slack_bot_token'])
sheets_service = initialize_sheets_service(config['google_service_account_info'])
TEMPLATE_SHEET_ID = "1hALS2c3KUdb3A6tGYaOZAe_WlV9Km241mDwsTE30rso"

tab_mapping = {
    "acceptance_criteria": "Acceptance Criteria - Use Cases",
    "regression_tests": "Regression Tests - Impacted Features",
    "performance": "Performance",
    "security": "Security",
    "api": "API",
    "browser_specific": "Browser Specific",
    "usability": "Usability",
    "backward_compatibility": "Backward Compatibility",
    "migration": "Migration",
}

@app.route('/')
def index():
    return 'Welcome to My Test Plan Creator!'

@app.route('/slack/events', methods=['POST'])
def slack_events():
    # Extract headers and body of the request from Slack
    signature = request.headers.get('X-Slack-Signature')
    timestamp = request.headers.get('X-Slack-Request-Timestamp')
    request_body = request.get_data(as_text=True)

    # Verify the request to ensure it came from Slack
    if not verify_slack_signature(request_body, timestamp, signature, config['slack_signing_secret']):
        return jsonify({'message': 'Invalid signature'}), 401
    
    # Slack sends a challenge request to verify the URL - we need to respond with the challenge value
    if request.json.get('type') == 'url_verification':
        return jsonify({'challenge': request.json['challenge']})
    
    # Handle the event payload from Slack
    event_data = request.json.get('event', {})
    if event_data.get('type') == 'app_home_opened':
        user = event_data.get('user')
        if user:
            publish_app_home(user, slack_client)

    # Only process message events from users or if the bot is mentioned
    if event_data.get('type') == 'message' and not event_data.get('subtype'):
        handle_slack_event(event_data)
    
    # Respond to Slack that the event was received
    return jsonify({'status': 'Event received'}), 200

@app.route('/slack/interactions', methods=['POST'])
def slack_interactions():
    payload = json.loads(request.form.get("payload"))
    user_id = payload['user']['id']
    channel_id = payload['container']['channel_id']

    if payload['type'] == 'block_actions':
        for action in payload['actions']:
            if action['action_id'] == "submit_tabs":
                # The format of `state` may vary, logging to see the structure
                selected_tabs = []
                state_values = payload['state']['values']
                for block_id, block_state in state_values.items():
                    for action_id, action_state in block_state.items():
                        if action_state['type'] == 'checkboxes':  # Found our checkboxes action
                            selected_tabs.extend([
                                option['value'] for option in action_state['selected_options']
                            ])
                
                with state_lock:
                    user_state = conversation_states.get(user_id, {})
                    user_state['selected_tabs'] = selected_tabs
                    user_state['status'] = 'tabs_selected'
                    conversation_states[user_id] = user_state

                # After updating the state, we acknowledge the tab selection
                send_slack_message(slack_client, channel_id, "Tab selections have been received. Processing the details...")
                # Now, you can call handle_slack_event here or from another trigger
                handle_slack_event({
                    'type': 'message',
                    'user': user_id,
                    'text': '',
                    'channel': channel_id,
                    'event_ts': payload['container']['message_ts']
                })
    # Respond to the interaction with an empty body to acknowledge
    return jsonify({}), 200    

def handle_slack_event(event_data):
    global conversation_states
    
    user_id = event_data['user']
    channel_id = event_data['channel']
    text = event_data.get('text', '').strip()
    event_ts = event_data.get('event_ts', '')

    with state_lock:
        # Fetch the user state, or create a new state if it doesn't exist
        user_state = conversation_states.setdefault(
            user_id, {
                'status': 'new',
                'feature_details': None,
                'selected_tabs': None,
                'last_event_ts': '0',
                'last_bot_message': None
                })

        # If the received event is older than the last event processed for the user, discard it
        if event_ts <= user_state['last_event_ts']:
            return
        
        # Update the last event timestamp to the current event's timestamp
        user_state['last_event_ts'] = event_ts
        
        if escape_html(text) == user_state['last_bot_message']:
            # Prevent sending the same message repeatedly
            return

        if is_greeting(text) and user_state['status'] in ['new', 'greeted']:
            send_greeting(channel_id, user_id)
            user_state['status'] = 'greeted'
            
        elif user_state['status'] == 'greeted' or (user_state['status'] == 'awaiting_feature_info' and not user_state['feature_details']):
                feature_name, feature_details, acceptance_criteria = parse_feature_text(text)
                user_state['feature_details'] = (feature_name, feature_details, acceptance_criteria)
                user_state['status'] = 'awaiting_tab_selection'
                ask_for_tabs_update(channel_id, user_id)
                
        # Check if tabs are selected and feature details have been provided
        if user_state['status'] == 'tabs_selected' and user_state['feature_details'] is not None:
            feature_name, feature_details, acceptance_criteria = user_state['feature_details']
            selected_tabs = user_state['selected_tabs']
            process_feature_details(channel_id, user_id, selected_tabs, feature_name, 
                                    feature_details, acceptance_criteria)

        conversation_states[user_id] = user_state  # Save state changes

def process_feature_details(channel_id, user_id, selected_tabs, feature_name, 
                                    feature_details, acceptance_criteria):
    global conversation_states

    # Assume the role just before the AWS service call
    role_arn = "arn:aws:iam::511738828901:role/test-plan-creator"  
    external_id = "test-plan-creator" 

    session_credentials = assume_role(role_arn, external_id)
    if session_credentials:
        aws_access_key_id_temp = session_credentials['AccessKeyId']
        aws_secret_access_key_temp = session_credentials['SecretAccessKey']
        aws_session_token_temp = session_credentials['SessionToken']

        new_sheet_id = duplicate_template_sheet(config['google_service_account_info'], TEMPLATE_SHEET_ID, feature_name)
        print("new_sheet_id:", new_sheet_id)
        
        for tab in selected_tabs:
            tab_name = tab_mapping[tab] 
            send_slack_message(slack_client, channel_id, f"Getting test cases for {tab_name} tab")
            prompt = build_claude_prompt(feature_name, feature_details, acceptance_criteria, tab_name)
            raw_response = invoke_claude(prompt, aws_access_key_id_temp, aws_secret_access_key_temp, aws_session_token_temp)
            print("raw_response:", raw_response)
            send_slack_message(slack_client, channel_id, f"Successfully built test cases for {tab_name} tab")
            parsed_data = parse_claude_response(raw_response)  # This function should return a 2D array
            # Find the tab in the spreadsheet and update it with parsed data
            last_col_num = len(parsed_data[0])
            end_column_letter = chr(ord('A') + last_col_num - 1)
            formatted_range = f"'{tab_name}'!A3:{end_column_letter}{len(parsed_data) + 2}"  # +2 to account for header rows
            print("formatted_range:", formatted_range)
            update_sheet_with_data(sheets_service, new_sheet_id, formatted_range, parsed_data)  


        sheet_url = f"https://docs.google.com/spreadsheets/d/{new_sheet_id}"
        sheet_message = f"Here's the Google Sheet with test cases: {sheet_url}"
        send_slack_message(slack_client, channel_id, sheet_message)    

        user_state = conversation_states.get(user_id, {})
        user_state['last_bot_message'] = sheet_message
        user_state['status'] = 'new'
        conversation_states[user_id] = user_state   

def send_greeting(channel_id, user_id):
    global conversation_states

    welcome_message = (
        ":wave: Hi! Welcome to Test Plan Creator.\n"
        "Please provide the following details in this format:\n\n"
        "Feature name: <name>\n"
        "Feature details: <details>\n"
        "Acceptance criteria: <criteria>"
    )
    send_slack_message(slack_client, channel_id, welcome_message)

    user_state = conversation_states.get(user_id, {})
    user_state['last_bot_message'] = welcome_message
    conversation_states[user_id] = user_state

def escape_html(text):
    return html.unescape(text) 

def ask_for_tabs_update(channel_id, user_id):
    blocks = [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": "Please select the tabs to update with test cases:"}
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": " "},  # This `text` is required, but the space will not show.
            "accessory": {
                "type": "checkboxes",
                "options": [
                    {"text": {"type": "plain_text", "text": "Acceptance Criteria - Use Cases"}, "value": "acceptance_criteria"},
                    {"text": {"type": "plain_text", "text": "Regression Tests - Impacted Features"}, "value": "regression_tests"},
                    {"text": {"type": "plain_text", "text": "Performance"}, "value": "performance"},
                    {"text": {"type": "plain_text", "text": "Security"}, "value": "security"},
                    {"text": {"type": "plain_text", "text": "API"}, "value": "api"},
                    {"text": {"type": "plain_text", "text": "Browser Specific"}, "value": "browser_specific"},
                    {"text": {"type": "plain_text", "text": "Usability"}, "value": "usability"},
                    {"text": {"type": "plain_text", "text": "Backward Compatibility"}, "value": "backward_compatibility"},
                    {"text": {"type": "plain_text", "text": "Migration"}, "value": "migration"},
                ],
                "action_id": "tab_selection",
            },
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Submit"},
                    "value": "submit_tabs",
                    "action_id": "submit_tabs",
                },
            ],
        },
    ]

    fallback_text = 'Please select the tabs to update with test cases.'
    try:
        response = slack_client.chat_postMessage(
            channel=channel_id,
            text=fallback_text, 
            blocks=blocks
            )
    except SlackApiError as e:
        print(f"Error sending interactive message: {e.response['error']}")


if __name__ == '__main__':
    app.run(debug=True)  