from FileHelper import *

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from dateutil.parser import parse
import datetime
import traceback
import schedule
import time

SCOPES_forms = ["https://www.googleapis.com/auth/forms.responses.readonly", "https://www.googleapis.com/auth/forms.body.readonly"]
credentials_path = "api_credentials/forms"

def forms():
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
        try: 
            proccess_cafeteria_menu(service)
        except:
            traceback.print_exc()



    except HttpError as error:
        # TODO(developer) - Handle errors from drive API.
        print(f'An error occurred: {error}')

def generate_specific_question_mapping(question, ID_value, question_type):
    item_mapping = {}
    item_mapping["Item_ID"] = ID_value
    item_mapping["Type"] = question_type
    return item_mapping
    mappings[item_title_question["questionItem"]["question"]["questionId"]] = item_title_mapping

def generate_cafeteria_form_mappings(form_content):
    mappings = {}
    group_titles = ["Menu Item #1", "Menu Item #2", "Menu Item #3", "Menu Item #4", "Menu Item #5", "Menu Item #6", "Menu Item #7", "Menu Item #8"]

    itemIndex = 0
    for item in form_content["items"]:
        if item["title"] in group_titles:
            item_title_question = form_content["items"][itemIndex + 1]
            item_price_question = form_content["items"][itemIndex + 2]
            item_day_question = form_content["items"][itemIndex + 3]

            # ID for question group (aka the three questions that describe a menu item)
            ID_value = group_titles.index(item["title"])

            # Create mappings
            mappings[item_title_question["questionItem"]["question"]["questionId"]] = generate_specific_question_mapping(item_title_question, ID_value, "Item_Title")
            mappings[item_price_question["questionItem"]["question"]["questionId"]] = generate_specific_question_mapping(item_price_question, ID_value, "Item_Price")
            mappings[item_day_question["questionItem"]["question"]["questionId"]] = generate_specific_question_mapping(item_day_question, ID_value, "Item_Days")
            


        itemIndex += 1
    
    return mappings

def get_multiple_choice_answer_as_array(raw_answer):
    output = []
    for answer in raw_answer["textAnswers"]["answers"]:
        output.append(answer["value"])
    return output

def get_text_answer(raw_answer):
    return raw_answer["textAnswers"]["answers"][0]["value"]

def proccess_cafeteria_menu(forms_service):
    print("|=================|\nChecking Cafeteria Form at Server Time " + datetime.datetime.now().isoformat())

    # Use forms api to get latest response
    form_id = "1zUo5VsquA9UjJ2pBCJC0O3D2GAp5fQA9Oks92r2BXPU"
    #queryString = "filter timestamp 2024-09-21T19:53:54.997Z"
    result = forms_service.forms().responses().list(formId=form_id).execute()

    startdt = datetime.datetime(2020, 1, 1)
    startdt = startdt.replace(tzinfo=datetime.timezone.utc)
    latestResponse = {"lastSubmittedTime": startdt}
    for response in result["responses"]:
        time_parsed = parse(response["lastSubmittedTime"], fuzzy=True)
        if time_parsed > latestResponse["lastSubmittedTime"] or response["lastSubmittedTime"] == "":
            response["lastSubmittedTime"] = time_parsed
            latestResponse = response

    # Load access data
    gforms_access_data = load_data_file("data/gforms_access_data.json")

    # Ensure defaults for all needed values exist
    if "last_accessed_time" not in gforms_access_data:
        gforms_access_data["last_accessed_time"] = startdt.isoformat()
    
    if "force_gforms_refresh" not in gforms_access_data:
        gforms_access_data["force_gforms_refresh"] = False
    
    last_accessed_time = datetime.datetime.fromisoformat(gforms_access_data["last_accessed_time"])


    if gforms_access_data["force_gforms_refresh"] == True:
        print("-> A data rebuild was requested.")


    # If need to parse new form submission
    if latestResponse["lastSubmittedTime"] > last_accessed_time or gforms_access_data["force_gforms_refresh"] == True:
        print("-> Performing Retrieval of Cafeteria Form Response.")

        last_accessed_time = latestResponse["lastSubmittedTime"]

        # Generate mappings for question IDs
        form_content = forms_service.forms().get(formId=form_id).execute()
        cafeteria_form_mappings = generate_cafeteria_form_mappings(form_content)
        #print("Mappings: " + json_to_formatted_string(cafeteria_form_mappings))

        cafeteria_data = []
        cafeteria_data_raw = {}

        # Parse response to raw data
        for questionID, answerValue in latestResponse["answers"].items():
            if questionID in cafeteria_form_mappings:
                mapped_question = cafeteria_form_mappings[questionID]
                if mapped_question["Item_ID"] not in cafeteria_data_raw:
                        cafeteria_data_raw[mapped_question["Item_ID"]] = {}

                if mapped_question["Type"] == "Item_Title":
                    cafeteria_data_raw[mapped_question["Item_ID"]]["Item_Title"] = get_text_answer(answerValue)
                elif mapped_question["Type"] == "Item_Price":
                    cafeteria_data_raw[mapped_question["Item_ID"]]["Item_Price"] = get_text_answer(answerValue)
                elif mapped_question["Type"] == "Item_Days":
                    cafeteria_data_raw[mapped_question["Item_ID"]]["Item_Days"] = get_multiple_choice_answer_as_array(answerValue)

            else:
                print("-> Error: Found questionID with no corresponding mapping: " + str(questionID))

        #print("\nRaw data is: " + json_to_formatted_string(cafeteria_data_raw))

        # Parse raw data to final format
        for menuItem in cafeteria_data_raw.values():
            formatted_menu_item = {}
            formatted_menu_item["Price"] = menuItem["Item_Price"]
            formatted_menu_item["Item"] = menuItem["Item_Title"]

            # Try finding day in final data
            for day in menuItem["Item_Days"]:
                found_day_entry = False
                for outputDayEntry in cafeteria_data:
                    if outputDayEntry["Day"] == day:
                        found_day_entry = True
                        outputDayEntry["Items"].append(formatted_menu_item)

                        break
                
                if not found_day_entry:
                    new_day_entry = {}

                    # Init new day entry in output data
                    new_day_entry["Day"] = day
                    new_day_entry["Items"] = []

                    new_day_entry["Items"].append(formatted_menu_item)

                    cafeteria_data.append(new_day_entry)

        print("-> Final data:\n" + json_to_formatted_string({"cafeteria_data": cafeteria_data}))

        output_data_final = {}
        output_data_final["cafeteria_data"] = cafeteria_data
        dump_data_file(output_data_final, "data/gforms_output_data.json")

        print("-> Finished Retrieving Latest Response.")

        

    # Write data back to dictionary
    gforms_access_data["last_accessed_time"] = last_accessed_time.isoformat()

    gforms_access_data["force_gforms_refresh"] = False

    # Save data to disk
    dump_data_file(gforms_access_data, "data/gforms_access_data.json")

    print("Forms Retrieval Completed\n|=================|")
    
# run once on startup
forms()

schedule.every(20).minutes.do(forms)

while True:
    schedule.run_pending()
    time.sleep(10)