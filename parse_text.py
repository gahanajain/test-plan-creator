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
