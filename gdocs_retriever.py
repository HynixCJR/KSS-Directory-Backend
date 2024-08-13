from __future__ import print_function

import os
import json

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import dotenv_values

from time import gmtime, strftime
import schedule
import time

from gdocs_retriever_parsing import scrape_doc

SCOPES_docs = ['https://www.googleapis.com/auth/documents.readonly']


def docs(doc_id):
    """Shows basic usage of the Docs API.
    Prints the title of a sample document.
    """

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('api_credentials/docs/token.json'):
        creds = Credentials.from_authorized_user_file('api_credentials/docs/token.json', SCOPES_docs)
        
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('api_credentials/docs/credentials.json', SCOPES_docs)
            creds = flow.run_local_server(port=0)
            # Enable offline access and incremental authorization
            authorization_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true'
            )
        # Save the credentials for the next run
        with open('api_credentials/docs/token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('docs', 'v1', credentials=creds)

        # Retrieve the documents contents from the Docs service.
        document = service.documents().get(documentId=doc_id).execute()
        images = 0
        inlineObjects = document.get('inlineObjects')
        if inlineObjects:
            images = {}
            for imageID, imageValues in inlineObjects.items():
                images[imageID] = imageValues["inlineObjectProperties"]["embeddedObject"]["imageProperties"]["contentUri"]
        return [document.get('body'), images]
    except HttpError as err:
        print(err)

def main_function():
    '''the main function of the gdocs retriever, which is set to run every 20 minutes.'''

    # If modifying these scopes, delete the file token.json.
    SCOPES_drive = ['https://www.googleapis.com/auth/drive.metadata.readonly']

    # Load existing variables from the .env.shared file
    env_vars_shared = dotenv_values('.env.shared')
    permitted_drive_folder_id = env_vars_shared['permitted_drive_folder_id']

    def latest_date(date1, date2):
        '''Returns the latest date of the two that are inputted.'''
        dates = []
        for i in [date1, date2]:
            newDate = ""
            for k in i:
                if str(k) in ['0','1','2','3','4','5','6','7','8','9']:
                    newDate += str(k)
            dates.append(newDate)
        if int(dates[0]) >= int(dates[1]):
            return date1
        else:
            return date2

    def drive():
        """Shows basic usage of the Drive v3 API.
        Prints the names and ids of the first 10 files the user has access to.
        """

        global items_under_permitted_folder
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('api_credentials/drive/token.json'):
            creds = Credentials.from_authorized_user_file('api_credentials/drive/token.json', SCOPES_drive)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'api_credentials/drive/credentials.json', SCOPES_drive)
                creds = flow.run_local_server(port=8080)
                # Enable offline access and incremental authorization
                authorization_url, state = flow.authorization_url(
                    access_type='offline',
                    include_granted_scopes='true'
                )
            # Save the credentials for the next run
            with open('api_credentials/drive/token.json', 'w') as token:
                token.write(creds.to_json())

        try:
            service = build('drive', 'v3', credentials=creds)

            # Call the Drive v3 API
            results = service.files().list(
                pageSize=1000, fields="nextPageToken, files(id, name, parents, modifiedTime, size)").execute()
            items = results.get('files', [])

            if not items:
                print('No files found.')
                return
            items_under_permitted_folder = []

            def check_file_children_id(parent_folder_id):
                '''checks if the specified folder ID is the parent ID of any item in the items var'''
                folders_within_parent = []
                for i in items:
                    if 'parents' in i and parent_folder_id in i['parents'] and 'size' in i:
                        # if the item is not a folder itself, and their parent is the same as parent_folder_id, then append it to items_under_permitted_folder
                        items_under_permitted_folder.append(i)
                    elif 'parents' in i and parent_folder_id in i['parents'] and 'size' not in i:
                        # if item IS a folder, and parent is same as parent_folder_id, then append it to folders_within_parent
                        folders_within_parent.append(i)
                return folders_within_parent

            folder_children = check_file_children_id(permitted_drive_folder_id)
            while True:
                if folder_children == []:
                    break
                else:
                    # if there are items in the folder_children list, i.e. there are still parent folders.
                    while True:
                        for i in folder_children:
                            new_folder_children = check_file_children_id(i['id'])
                            folder_children.remove(i)
                            if 'size' not in i:
                                if new_folder_children != []:
                                    for k in new_folder_children:
                                        folder_children.append(k)
                        if folder_children == []:
                            break
                    break



        except HttpError as error:
            # TODO(developer) - Handle errors from drive API.
            print(f'An error occurred: {error}')


    current_docs = {}
    # the current docs folder dict is used so that i can check if certain docs have been removed.
    # it follows the format {doc_id: [<discord_tag>, file_path]}

    print("|=================|\nBeginning Google Drive Retrieval. Last retrieval time was: " + env_vars_shared['last_retrieved_time'])

    with open("gdocs_retriever_access_data.json", "r+") as access_data_file: 
        access_data = json.load(access_data_file)
        new_access_data = {}
        new_access_data["previousModifiedTimes"] = {}

        if "previousModifiedTimes" not in access_data or env_vars_shared['force_gdocs_refresh'] == "True":
            access_data["previousModifiedTimes"] = {}

    drive()
    files_updated = 0
    for item in items_under_permitted_folder:
        document_modified_time_formatted = item["modifiedTime"][0:19]
        if item["name"] in access_data["previousModifiedTimes"]:
            previous_modified_time = access_data["previousModifiedTimes"][item["name"]]
        else:
            previous_modified_time = "none"

        print("|-----------------|\nParsing file metadata for file: " + item["name"] + "\n-> Last modified time: " + document_modified_time_formatted + "\n-> Previous last modified time: " + previous_modified_time)
        
        if previous_modified_time != document_modified_time_formatted:
            # if the doc was last edited after the docs were last retrieved, then retrieve the doc again.
            full_doc_and_imgs = docs(item['id'])
            full_doc = full_doc_and_imgs[0]["content"][1:]
            doc_images = full_doc_and_imgs[1]
            current_docs[item['id']] = scrape_doc(full_doc, doc_images, document_modified_time_formatted)
            
            print("A Google Docs retrieval was completed.\n" + "-> Doc name: " + item['name'] + "\n-> File ID: " + item['id'] + "\n-> Last modified time: " + item['modifiedTime'])
            
            files_updated += 1

        new_access_data["previousModifiedTimes"][item["name"]] = document_modified_time_formatted

    # for path in os.listdir("club_info_pages"):
    #     # iterate through the club_info_pages dir to get each folder
    #     if path != ".keep":
    #         for file in os.listdir("club_info_pages/" + path):
    #             # iterate through each folder in the club_info_pages folder
    #             remove_file = True
    #             for index, current_file in current_docs.items():
    #                 # iterate through the current_docs dict and see if the file currently in the local directory is in the retrieved files.
    #                 # if not, then keep remove_file as True, and thus remove the file from the current local directory.
    #                 if "club_info_pages/" + path + "/" + file == current_file[1]:
    #                     remove_file = False
    #                     break
    #             if remove_file == True:
    #                 print("removing file at club_info_pages/" + path + "/" + file)
    #                 # os.remove("club_info_pages/" + path + "/" + file)
    #                 # this line doesn't work when I run on Windows, so I'm just gonna pray it works on the linux server.

    with open("gdocs_retriever_access_data.json", "r+") as access_data_file:
        access_data_file.truncate(0) # clear file
        json.dump(new_access_data, access_data_file)

    print("|-----------------|\nGoogle Drive Retrieval Completed at server time of " + strftime("%Y-%m-%dT%H:%M:%S", gmtime()) + ", with " + str(files_updated) + " file(s) updated.")

    with open('.env.shared', 'w+') as env_vars:
        # removing everything in the .env.shared file
        env_vars.write("")

    # set last_retrieved_time to the current time
    env_vars_shared["last_retrieved_time"] = strftime("%Y-%m-%dT%H:%M:%S", gmtime())
    # reset refresh flag - ensure it won't do a full refresh next time
    env_vars_shared["force_gdocs_refresh"] = False

    for key, value in env_vars_shared.items():
        # add everything new that is in env_vars_shared to the now empty .env.shared file.
        with open('.env.shared', 'a') as env_vars:
            env_vars.write(f"{key}={value}\n")

main_function()
# run the function once for diagnostic purposes.

# repeats the docs retrieval of the example doc every 12 hours, so that the token won't expire
def update_docs_token():
    a = docs("1kris6JV48ESIK0ucat7zS66-YfkA_NnsSol4qrQ-IjE")
schedule.every(12).hours.do(update_docs_token)

# repeats the whole function every 20 minutes
schedule.every(20).minutes.do(main_function)



while True:
    schedule.run_pending()
    time.sleep(10)