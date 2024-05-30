import re

def is_greeting(text):
    return text.lower() == "hi"

def remove_curly_brace_pairs(input_text):
    # This regex will match pairs of curly braces with anything in between, non-greedy
    pattern = re.compile(r'\{.*?\}')
    return re.sub(pattern, '', input_text)

def parse_claude_response(raw_response):
    if raw_response is None:
        raise ValueError("The response from Claude is empty. Cannot parse an empty response.")

    raw_response = raw_response.replace('<br>', '[BR_TOKEN]').replace('\n', '[NL_TOKEN]')
    lines = raw_response.split('[NL_TOKEN]')
    data = []

    # Flags to identify if we are inside a table
    header_found = False
    table_started = False

    for i, line in enumerate(lines):
        if '|' in line:
            # Replace tokens with actual newline characters to preserve the formatting inside the cells
            line = line.replace('[BR_TOKEN]', '\n')

            # Check for the header row based on the presence of '| --- |'
            if '---' in line and '|' in lines[i-1]:
                header_found = True
                # Strip leading and trailing '|', then split using '|' and strip each cell value
                headers = [cell.strip() for cell in lines[i-1].strip('|').split('|')]
                data.append(headers)  # Append headers to the data
                continue
            
            # Check if this could be a content row based on whether we already found a header
            if header_found and '|' in line:
                table_started = True
                row_data = [cell.strip() for cell in line.strip('|').split('|')]
                data.append(row_data)
            elif table_started:
                # Once table content has started, break out at the first row without '|'
                break

    if not data or not header_found:
        raise ValueError("No markdown table data found in the response")

    return data
