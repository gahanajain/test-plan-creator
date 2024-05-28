import re

def parse_feature_text(text):
    print('parse_feature_text')
    print("Input to parse_feature_text:", repr(text))

    # Regex pattern that looks for the headings in a case-insensitive manner
    pattern = {
        'name': re.compile(r"Feature\s+name\s*[-:]\s*(.+)", re.I),
        'details': re.compile(r"Feature\s+details\s*[-:]\s*(.+?)\n(?=Feature|$)", re.I | re.DOTALL),
        'criteria': re.compile(r"Acceptance\s+criteria\s*[-:]?\s*(.+?)\n(?=Feature|$)", re.I | re.DOTALL),
    }

    feature_name = 'N/A'
    feature_details = 'N/A'
    acceptance_criteria = 'N/A'

    # Search for feature name, details, and acceptance criteria in the provided text
    name_match = pattern['name'].search(text)
    if name_match:
        feature_name = name_match.group(1).strip()

    details_match = pattern['details'].search(text)
    if details_match:
        feature_details = details_match.group(1).strip()

    criteria_match = pattern['criteria'].search(text)
    if criteria_match:
        acceptance_criteria = criteria_match.group(1).strip()

    if feature_name == 'N/A' and feature_details == 'N/A' and acceptance_criteria == 'N/A':
        raise ValueError("The text format is incorrect or missing required fields.")

    return feature_name, feature_details, acceptance_criteria
 

def is_greeting(text):
    return text.lower() == "hi"

def send_parsing_error_message(channel_id, user_id):
    print('send_parsing_error_message')
    global conversation_states
    error_message = "The text format is incorrect or missing required fields.\n"\
                    "Please provide feature information in this format:\n"\
                    "*Feature name*: <name>\n"\
                    "*Feature details*: <details>\n"\
                    "*Acceptance criteria* (optional): <criteria>"
    send_slack_message(slack_client, channel_id, error_message)

    user_state = conversation_states.get(user_id, {})
    user_state['last_bot_message'] = error_message
    conversation_states[user_id] = user_state  

def parse_claude_response(raw_response):
    if raw_response is None:
        raise ValueError("The response from Claude is empty. Cannot parse an empty response.")

    # Split the raw response into lines
    lines = raw_response.strip().split('\n')
    
    # Initialize an empty list to hold the parsed table rows
    data = []

    # Iterate over the lines using an index so we can also check the following line
    for i, line in enumerate(lines[:-1]):  # Skip the last line to avoid IndexError
        stripped_line = line.strip()
        
        # Check if this line could be a header based on | and the next line has --- separators
        if "|" in stripped_line and "---" in lines[i + 1]:
            # If the next line after the header is empty or also includes | characters, we treat it as part of the table
            if lines[i + 1].strip() == "" or "|" in lines[i + 2]:
                # The content should start after the header and optional separator
                start_index = i + 1 if lines[i + 1].strip() == "" else i + 2
                for table_line in lines[start_index:]:
                    # If the line starts and ends with |, then it's a content row of the table
                    if table_line.startswith("|") and table_line.endswith("|"):
                        # Split cells, remove leading/trailing spaces, and exclude first/last element if empty
                        cells = [cell.strip() for cell in table_line.split("|")[1:-1]]
                        data.append(cells)
                    else:
                        # The table content has ended, break out of the loop
                        break
                break  # Break the main loop after processing the table

    if not data:
        raise ValueError("No markdown table data found in the response")

    return data