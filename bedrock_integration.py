import boto3
import json
from botocore.exceptions import ClientError

# Initialize the Bedrock client for Claude model invocation

modelId = "anthropic.claude-3-haiku-20240307-v1:0"  # Replace with your actual model ID
accept = "application/json"
content_type = "application/json"

def invoke_claude(prompt, aws_access_key_id, aws_secret_access_key, aws_session_token):
    """
    Sends prompt to Claude API and returns the response.
    Args:
        prompt (str): Prompt string to send to Claude.
    Returns:
        str: The text of Claude's response.
    """
    # Initialize the Bedrock client with the temporary credentials
    bedrock = boto3.client(
        service_name="bedrock-runtime",
        region_name='us-west-2',
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        aws_session_token=aws_session_token
    )

    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 4096,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
    }

    try:
        response = bedrock.invoke_model(
            modelId=modelId,
            body=json.dumps(request_body),
        )

        # Process and return the response
        result = json.loads(response.get("body").read())
        output_list = result.get("content", [])
        # Assuming the response content is the one you need
        return output_list[0]["text"] if output_list else ''

    except ClientError as e:
        print(f"Couldn't invoke model. Error: {e.response['Error']}")
        raise

def build_claude_prompt(feature_name, feature_details, acceptance_criteria, tab):
    """
    Construct prompt text based on provided details for Claude.
    """

    tab_prompts = {
        "Acceptance Criteria - Use Cases": f""" Human: Generate as many test cases as possible in tabular form for {feature_name} ensuring that all user scenarios are covered.
            Feature details: {feature_details}, 
            Acceptance Criteria: {acceptance_criteria}
            The table should only include columns: S.No, Test Case Description, Priority (P0-high, P1-medium, P2-low), Test steps, and Expected Outcomes.
            Do not include any introductory text, explanations, or comments outside of the table.
            Do not just limit to 10 test cases, build as many test cases as possible with all possible combinations.
            Start your table immediately after this line and exclude any non-table text.
            The response should be in markdown format, starting immediately below a header row like this:
            | S.No | Test Case Description | Priority | Test Steps | Expected Outcomes |
            | --- | --- | --- | --- | --- |
            Assistant: """,

        "Regression Tests - Impacted Features": f""" Human:  Generate as many test cases as possible for potential regression in tabular form for features that might be impacted by {feature_details}.
            Feature details: {feature_details}, 
            Acceptance Criteria: {acceptance_criteria}
            Focus on areas of the application that are most likely to be affected and detail the steps required to verify that existing functionality is still working as expected.
            The table should only include an S.No, Test Case Description, Priority (P0-high, P1-medium, P2-low), Test steps, and Expected Outcomes.
            Do not include any introductory text, explanations, or comments outside of the table. "
            Start your table immediately after this line and exclude any non-table text.
            The response should be in markdown format, starting immediately below a header row like this:
            | S.No | Test Case Description | Priority | Test Steps | Expected Outcomes |
            | --- | --- | --- | --- | --- |
            Assistant: """,

        "Performance": f""" Human:  Generate as many test cases as possibl to outline performance test scenarios in tabular form that assess the responsiveness, stability, and speed of {feature_details}.
            Feature details: {feature_details}, 
            Acceptance Criteria: {acceptance_criteria}
            Describe the setup, tools required to measure, expected metrics, and how to simulate load or stress conditions.
            The table should only include an S.No, Test Case Description, Priority (P0-high, P1-medium, P2-low), Test steps, and Expected Outcomes.
            Do not include any introductory text, explanations, or comments outside of the table. "
            Start your table immediately after this line and exclude any non-table text.
            The response should be in markdown format, starting immediately below a header row like this:
            | S.No | Test Case Description | Priority | Test Steps | Expected Outcomes |
            | --- | --- | --- | --- | --- |
            Assistant: """,

        "Security": f""" Human: Generate as many test cases as possible in tabular form covering comprehensive security verification of {feature_details} including role-based access control, cross-organization data isolation, common attack vectors like XSS, SQL injection, and any potential vulnerabilities related to data exposure.
            Feature details: {feature_details}, 
            Acceptance Criteria: {acceptance_criteria}
            The table should include an S.No, Category, Test Case Description, Priority (P0-high, P1-medium, P2-low), Test steps, and Expected Outcomes. 
            Do not include any introductory text, explanations, or comments outside of the table. "
            Start your table immediately after this line and exclude any non-table text.
            The response should be in markdown format, starting immediately below a header row like this:
            | S.No | Category | Test Case Description | Priority | Test Steps | Expected Outcomes |
            | --- | --- | --- | --- | --- | --- |
            Assistant: """,

        "API": f""" Human: If {feature_details} includes API changes, provide API test cases in tabular form that validate both positive paths and error cases. 
            Generate as many test cases as possible.
            Feature details: {feature_details}, 
            Acceptance Criteria: {acceptance_criteria}
            Include tests for request and response integrity, error handling, and adherence to RESTful principles if applicable. Test cases should also consider boundary conditions and data validation.
            Test steps should include API to be used (if possible)
            The table should include an S.No, Test Case Description, Priority (P0-high, P1-medium, P2-low), Test steps, and Expected Outcomes. 
            Do not include any introductory text, explanations, or comments outside of the table. "
            Start your table immediately after this line and exclude any non-table text.
            The response should be in markdown format, starting immediately below a header row like this:
            | S.No | Test Case Description | Priority | Test Steps | Expected Outcomes |
            | --- | --- | --- | --- | --- |
            Assistant: """,

        "Browser Specific": f""" Human: Generate as many browser compatibility test cases as possible in tabular form that ensure {feature_details} works correctly on supported web browsers.
            Feature details: {feature_details}, 
            Acceptance Criteria: {acceptance_criteria}
            Include steps for checking functionality, layout, and user interactions.
            The table should include an S.No, Test Case Description, Priority (P0-high, P1-medium, P2-low), Test steps, and Expected Outcomes. 
            Do not include any introductory text, explanations, or comments outside of the table. "
            Start your table immediately after this line and exclude any non-table text.
            The response should be in markdown format, starting immediately below a header row like this:
            | S.No | Test Case Description | Priority | Test Steps | Expected Outcomes |
            | --- | --- | --- | --- | --- |
            Assistant: """,

        "Usability": f""" Human: Generate as many usability test cases as possible in tabular form that assess the user experience and interaction flow of {feature_details}.
            Feature details: {feature_details}, 
            Acceptance Criteria: {acceptance_criteria}
            Focus on intuitiveness, ease of use, and user satisfaction metrics.
            The table should include an S.No, Test Case Description, Priority (P0-high, P1-medium, P2-low), Test steps, and Expected Outcomes. 
            Do not include any introductory text, explanations, or comments outside of the table. "
            Start your table immediately after this line and exclude any non-table text.
            The response should be in markdown format, starting immediately below a header row like this:
            | S.No | Test Case Description | Priority | Test Steps | Expected Outcomes |
            | --- | --- | --- | --- | --- |
            Assistant: """,

        "Backward Compatibility": f""" Human: Generate as many test cases as possible in tabular form to ensure backward compatibility for {feature_details}, paying special attention to impacts on existing features, customer queries, and data handling.
            Feature details: {feature_details}, 
            Acceptance Criteria: {acceptance_criteria}
            Address any potential breaking changes and compatibility with previous versions.
            The table should include an S.No, Test Case Description, Priority (P0-high, P1-medium, P2-low), Test steps, and Expected Outcomes. 
            Do not include any introductory text, explanations, or comments outside of the table. "
            Start your table immediately after this line and exclude any non-table text.
            The response should be in markdown format, starting immediately below a header row like this:
            | S.No | Test Case Description | Priority | Test Steps | Expected Outcomes |
            | --- | --- | --- | --- | --- |
            Assistant: """,

        "Migration": f""" Human: Generate as many test cases as possible in tabular form to validate migration scenarios for {feature_details} including data migration integrity prior and post-migration, performance comparison, and the correctness of the data transformation process.
            Feature details: {feature_details}, 
            Acceptance Criteria: {acceptance_criteria}
            The table should include an S.No, Test Case Description, Priority (P0-high, P1-medium, P2-low), Test steps, and Expected Outcomes. 
            Do not include any introductory text, explanations, or comments outside of the table. "
            Start your table immediately after this line and exclude any non-table text.
            The response should be in markdown format, starting immediately below a header row like this:
            | S.No | Test Case Description | Priority | Test Steps | Expected Outcomes |
            | --- | --- | --- | --- | --- |
            Assistant: """
    }  

    if tab in tab_prompts:
        prompt_template = tab_prompts[tab]
        prompt = prompt_template.format(
            feature_name=feature_name,
            feature_details=feature_details,
            acceptance_criteria=acceptance_criteria
        )
        print("Prompt:", prompt)
        return prompt  # Return the formatted prompt for the specific tab

    # If the tab is not in the dictionary, raise an error or handle it accordingly
    raise ValueError(f"Prompt for tab '{tab}' does not exist.")