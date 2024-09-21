from FileHelper import *

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES_forms = ['https://www.googleapis.com/auth/documents.readonly']
credentials_path = "api_credentials/drive"

def login():
    creds = None

    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(credentials_path + '/token.json'):
        creds = Credentials.from_authorized_user_file(credentials_path + '/token.json', SCOPES_forms)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path + '/credentials.json', SCOPES_forms)
            creds = flow.run_local_server(port=0)
            # Enable offline access and incremental authorization
            authorization_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true'
            )
        # Save the credentials for the next run
        with open(credentials_path + '/token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('forms', 'v1', credentials=creds)

        # Use forms api

    except HttpError as error:
        # TODO(developer) - Handle errors from drive API.
        print(f'An error occurred: {error}')