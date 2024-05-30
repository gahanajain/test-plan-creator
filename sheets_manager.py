from googleapiclient.discovery import build
from google.oauth2 import service_account 
from googleapiclient.errors import HttpError

def initialize_sheets_service(service_account_info):
    """
    Initialize and return the Google Sheets service object.
    Args:
        service_account_info (dict): The service account info loaded from the JSON file.
    Returns:
        service: An authorized Google Sheets service object.
    """
    credentials = service_account.Credentials.from_service_account_info(service_account_info)
    service = build('sheets', 'v4', credentials=credentials)
    return service

def duplicate_template_sheet(service_account_info, template_id, new_title):
    """
    Duplicates the entire spreadsheet and returns the new spreadsheet's ID.
    
    Args:
        service_account_info (dict): The service account info for authorization.
        template_id (str): The ID of the template spreadsheet to duplicate.
        new_title (str): The title for the new, duplicated spreadsheet.

    Returns:
        str: The ID of the newly created, duplicated spreadsheet.
    """
    credentials = service_account.Credentials.from_service_account_info(service_account_info)
    drive_service = build('drive', 'v3', credentials=credentials)

    try:
        # Copy the spreadsheet
        copy_metadata = {'name': new_title}
        new_file = drive_service.files().copy(
            fileId=template_id, body=copy_metadata, fields='id', supportsAllDrives=True
        ).execute()

        # Retrieve and return the ID of the new spreadsheet
        new_spreadsheet_id = new_file.get('id')
        return new_spreadsheet_id

    except Exception as e:
        print(f"Error duplicating spreadsheet: {e}")
        raise

def update_sheet_with_data(service, spreadsheet_id, sheet_range, values):
    """
    Updates the specified range in a sheet with the given data.
    """
    try:
        body = {'values': values}
        result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=sheet_range,
            body=body,
            valueInputOption='USER_ENTERED'
        ).execute()
        
        # Parse the sheet name and get sheetId from the range to be used for auto-resizing the columns
        sheet_name = sheet_range.split('!')[0].strip("'")
        sheet_id = get_sheet_id_by_name(service, spreadsheet_id, sheet_name)
        
        # Auto-resize the columns
        if sheet_id is not None:
            autoresize_dimensions(service, spreadsheet_id, sheet_id)
        return result

    except HttpError as error:
        print(f"Error updating the sheet: {error}")
        raise

def autoresize_dimensions(service, spreadsheet_id, sheet_id):
    body = {
        "requests": [
            {
                "autoResizeDimensions": {
                    "dimensions": {
                        "sheetId": sheet_id,
                        "dimension": "COLUMNS",
                        "startIndex": 2,  
                    }
                }
            },
            {
                "autoResizeDimensions": {
                    "dimensions": {
                        "sheetId": sheet_id,
                        "dimension": "ROWS",
                        "startIndex": 2,  
                    }
                }
            }
        ]
    }
    response = service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id, body=body).execute()
    return response

def get_sheet_id_by_name(service, spreadsheet_id, sheet_name):
    spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    
    # Find the sheet by name and return its ID
    for sheet in spreadsheet.get('sheets', []):
        if sheet['properties']['title'] == sheet_name:
            return sheet['properties']['sheetId']
    return None    
