from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json
from FileHelper import *
import glob
import os, traceback
app = FastAPI()
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse

# For some reason the server wouldn't run without this code?
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class openAnce():
    """The class for opening announcements and returning them as JSON files"""

    def date(date):
        """Returns the announcement JSON file at the specified date. If there is none, the function returns 'none'."""
        try:
            print("announcements/" + date + ".json")
            anceData = open("announcements/" + date + ".json", "r")
            #print(anceData)
            ance = anceData.read()
            return json.loads(ance)
        except:
            traceback.print_exc()
            return "none"

    def batch(num, index):
        """Returns the most recent 'num' number of announcements, at index of 'index'."""
        # Also returns if that index is the last one or not
        # I also call this "batches" in my comments elsewhere
        ances = {}
        all_ance = sorted(glob.glob("announcements/*.json"))
        for i in range(len(all_ance) - num * (index), 0, -1):
            if len(ances) == num:
                break
            else:
                anceData = open(all_ance[i-1], "r", encoding='utf-8')
                ance = json.loads(anceData.read())
                #print(type(ance))
                
                clubColourDataRaw = load_data_file("data/pings.json")
                clubColourData = {}
                for [key, value] in clubColourDataRaw.items():
                    clubColourData[value[0]] = value[2]
                for [key, value] in ance.items():
                    if key != "0":
                        if value[1] in clubColourData:
                            ance[key].append(clubColourData[value[1]])
                        else:
                            ance[key].append("none")

                #print(ance)

                ances.update({len(all_ance) - i: ance})

        if len(ances) == 0:
            return "none"
        else:
            if len(all_ance) - num * (index + 1) <= 0:
                ances.update({"Last": True})
            else:
                ances.update({"Last": False})
            return ances
        
    def batchAnceNew(num, index):
        outputData = {}
        outputData["announcements"] = []
        all_announcements = sorted(glob.glob("announcements/*.json"))
        clubColourDataRaw = load_data_file("data/pings.json")

        for i in range(len(all_announcements) - num * (index), 0, -1):
            if len(outputData["announcements"]) == num:
                break
            else:
                with open(all_announcements[i-1], "r", encoding='utf-8') as anceData:
                    anceRaw = json.loads(anceData.read())

                    anceProcessedList = []
                    dateData = []
                    for key, value in anceRaw.items():
                        if key != "0":
                            category = value[0]
                            roleName = value[1]
                            anceTitle = value[2]
                            description = value[3]
                            clubColor = "266"

                            clubPingKey = ""
                            for pingKey, pingDataValue in clubColourDataRaw.items():
                                if pingDataValue[0] == roleName:
                                    clubColor = pingDataValue[2]
                                    clubPingKey = pingKey
                                    break

                            processedAnce = {}
                            processedAnce["category"] = category
                            processedAnce["roleName"] = roleName
                            processedAnce["anceTitle"] = anceTitle
                            processedAnce["description"] = description
                            processedAnce["clubColor"] = clubColor
                            processedAnce["clubPingKey"] = clubPingKey

                            anceProcessedList.append(processedAnce)
                        else:
                            dateData = value
                    # append day to list
                    outputData["announcements"].append({"date": dateData, "announcementData": anceProcessedList})

                


                

        if len(outputData) == 0:
            return "none"
        else:
            if len(all_announcements) - num * (index + 1) <= 0:
                outputData.update({"Last": True})
            else:
                outputData.update({"Last": False})
            return outputData
# HTTP get request for an announcement JSON file at specified date
@app.get("/ance/date/{date}")
def getAnce(date: str):
    return openAnce.date(date)

# HTTP request for a batch of JSON files at a specified index.
@app.get("/ance/batch/{num}/{index}")
def getAnceBatch(num: int, index: int):
    # takes in index with start point of 0
    return openAnce.batch(num, index)

# HTTP request for a batch of JSON files at a specified index.
# Only returns announcements matching the tag
@app.get("/ance/batch/{num}/{index}/{clubTag}")
def getAnceBatchSpecificCLub(num: int, index: int, clubTag: str):
    # takes in index with start point of 0
    data = openAnce.batchAnceNew(num, index)
    #print(clubTag)

    newDayList = []
    for day in data["announcements"]:
        newDayAnces = []

        for ance in day["announcementData"]:
            if ance["clubPingKey"] == clubTag:
                #print(ance["clubPingKey"])
                newDayAnces.append(ance)
        
        if len(newDayAnces) > 0:
            newDay = day
            newDay["announcementData"] = newDayAnces
            newDayList.append(newDay)

    if not len(newDayList) > 0:
        return "none"

    data["announcements"] = newDayList
    return data


@app.get("/anceTotal/{year}/{month}")
def anceTotal(year: str, month: str):
    # Returns the name of the announcements within the provided month.
    # Not the actual JSON files themselves.
    # This is specifically for the calendar preview, so it doesn't return the actual announcements.
    ances = []
    for i in glob.glob("announcements/" + year + month + "*.json"):
        print(i[14:22])
        ances.append(i[14:22])
    return ances

def formatClubRepoAsInfo(club_URL):
    '''Formats club repo data for display in announcement popups'''
    repoData = get_specific_club_repo_data(club_URL)
    if repoData == "none":
        return "none"
    
    clubInfo = {}
    clubInfo["Description"] = repoData["Basic_Info"]["Description"]
    
    links = []
    for k, v in repoData["Links"].items():
        links.append(v[1])
    if links != []:
        clubInfo["Socials"] = links

    if repoData["Basic_Info"]["Supervisors"] != "Unspecified":
        supervisors = []
        for supervisorID, supervisorData in repoData["Basic_Info"]["Supervisors"].items():
            supervisors.append(supervisorData)
        if supervisors != []:
            clubInfo["Supervisor(s)"] = ", ".join(supervisors)

    locations_unprocessed = []
    meeting_days_unprocessed = []
    for meeting in repoData["Meeting_Times"].values():
        #print(meeting)
        locations_unprocessed.append(meeting["Meeting_Location"])
        meeting_days_unprocessed.append(meeting["Meeting_Day"]);
    
    locations_out = []
    locations_set = set()
    for location in locations_unprocessed:
        if location.lower() not in locations_set:
            locations_set.add(location.lower())
            locations_out.append(location)
    clubInfo["Location"] = ", ".join(locations_out)

    if len(meeting_days_unprocessed) > 0:
        meeting_time_date_string = ", ".join(meeting_days_unprocessed)
        clubInfo["Meeting times/dates"] = meeting_time_date_string.title()


    clubInfo["Club_Repo_URL"] = repoData["Metadata"]["URL"]

    return clubInfo
    
    

@app.get("/clubinfo/{club}")
# Does not accept spaces, so spaces have to be changed to "$"
def getClubInfo(club: str):
    '''Gets the info of a specific club/event, returns as dictionary / json'''
    clubInfoProcessed = {}
    
    try:  
        clubInfoRaw = load_data_file("data/clubInfo.json")

        if club.replace("$", " ") not in clubInfoRaw:
            print("Requested club: '" + club.replace("$", " ") + "' was not in the database")
        else:
            clubInfoProcessed = clubInfoRaw[club.replace("$", " ")]
    except:
        traceback.print_exc()
        return "none"
    
    try:
        pingID = ""
        clubColour = 0

        clubColourData = load_data_file("data/pings.json")
        for clubPingID, clubColourValue in clubColourData.items():
            if clubColourValue[0] == club.replace("$", " "):
                #print("2:", clubColourValue)
                clubColour = clubColourValue[2]
                pingID = clubPingID
                break

        # Check if we have a club repo entry, if we do, overwrite clubInfoProcessed
        for category in get_club_repo_list_data():
            for clubName, clubData in category["Content"].items():
                # print(clubData["Tag"])
                if clubData["Tag"] == pingID and clubData["Published"] == "Yes":
                    clubInfoProcessed = formatClubRepoAsInfo(clubData["URL"])
                    print("> Overriding club data for club \"" + club.replace("$", " ") + "\" with club repo data.")
                    break
        
        
        clubInfoProcessed["Colour"] = clubColour

        if len(clubInfoProcessed) > 0:
            #print("3:", clubInfoProcessed)
            return clubInfoProcessed
        else:
            return "none"
    except:
        traceback.print_exc()
        return "none"

def get_specific_club_repo_data(club_URL:str):
    # for i in os.listdir("club_info_pages"):
    #     if i != ".keep" and os.path.isdir("club_info_pages/" + i):
    #         filepath = "club_info_pages/" + i + "/" + club_URL +  "/" + club_URL + ".json"
    #         if os.path.isfile(filepath):
    #             club_repo_info = load_data_file(filepath)
    #             if club_repo_info["Metadata"]["Published"].lower() == "yes" and club_repo_info["Metadata"]["URL"] == club_URL:
    #                 return club_repo_info
    clubCategoryData = load_data_file("static_data/categoryInfo.json")
    clubListData = load_data_file("club_info_pages/club_list.json")
    for club in clubListData.values():
        if club["URL"] == club_URL:
            if club["Published"].lower() == "yes":

                clubCategory = club["Category"].replace(" ", "_").lower()
                filepath = "club_info_pages/" + clubCategory + "/" + club_URL +  "/" + club_URL + ".json"
                if os.path.isfile(filepath):
                    club_repo_info = load_data_file(filepath)
                    if club_repo_info["Metadata"]["Published"].lower() == "yes" and club_repo_info["Metadata"]["URL"] == club_URL:
                        if clubCategory in clubCategoryData:
                            club_repo_info["Category_Metadata"] = clubCategoryData[clubCategory]
                        else:
                            club_repo_info["Category_Metadata"] = clubCategoryData["other_clubs"]
                            print("Error getting category data, requested category " + clubCategory + " was missing from the database!")
                        return club_repo_info
    
    return "none"

@app.get("/specific_club_repo/{club_URL}")
def get_specific_club_repo(club_URL:str):
    '''Retrieves the info for a specific club repository page.
    Images are not included; they must be retrieved from a separate get request.
    Does not return if club is not published.
    Listed status does not affect whether the page can be returned or not.'''
    try:
        return get_specific_club_repo_data(club_URL)
    except:
        traceback.print_exc()
        return "none"

@app.get("/club_repo_main")
def get_club_repo_main():
    '''Retrieves every single club info page, excluding images.
    This runs on build time for the landing club repo page.'''
    returned_list = []
    for i in os.listdir("club_info_pages"):
        if i != ".keep" and os.path.isdir("club_info_pages/" + i):
            for k in os.listdir("club_info_pages/" + i):
                returned_list.append({"Content": load_data_file("club_info_pages/" + i + "/" + k + "/" + k + ".json")})
                # if club_repo_info["Metadata"]["Published"].lower() == "yes":
                #     returned_list.append({"URL": club_repo_info["Metadata"]["URL"], "Content": club_repo_info})
    return returned_list

def get_club_repo_list_data():
    returned_data = {}
    clubListData = load_data_file("club_info_pages/club_list.json")
    clubCategoryData = load_data_file("static_data/categoryInfo.json")
    for club in clubListData.values():
        if club["Published"].lower() == "yes":
            if club["Category"] not in returned_data:
                returned_data[club["Category"]] = {"Content": {club["Club_Name"]: club}}

                # if "Metadata" not in returned_data[club["Category"]]:
                #     returned_data[club["Category"]]["Metadata"] = {}

                if club["Category"].replace(" ", "_").lower() in clubCategoryData:
                    returned_data[club["Category"]]["Metadata"] = clubCategoryData[club["Category"].replace(" ", "_").lower()]
                else: # Provide a suitable fallback
                    returned_data[club["Category"]]["Metadata"] = {"Order": 40, "Color": "#FFFFFF"}
                    print("Club " + club["Club_Name"] + " has invalid category: " + club["Category"])
                
            else:
                returned_data[club["Category"]]["Content"][club["Club_Name"]] = club

    returned_list = []
    for [category, catData] in returned_data.items():
        returned_list.append({"Category Name": category, "Metadata":catData["Metadata"], "Content":catData["Content"]})

    # print(returned_list)
    def compareCategoryOrder(val):
        return val["Metadata"]["Order"]

    returned_list.sort(key=compareCategoryOrder)
    #print(returned_list)

    return returned_list
    

@app.get("/club_repo_list")
def get_club_repo_list():
    '''Retrieves each club repo page's metadata including Name, Category, and URL.
    If the club repo is set to not be published, then it won't be returned.
    If the club repo is set to not be listed, then it will be returned, along with its listed status.'''
    try:
        return get_club_repo_list_data()
    except:
        traceback.print_exc()
        return "none"

@app.get("/specific_club_images/{club_URL}/{image_file_name}", response_class=FileResponse)
def retrieve_specific_club_images(club_URL: str, image_file_name : str, hash : str = None):
    '''retrieves a single image from within the club_info_pages directory, if they are available.'''

    defaultLogo = "static_data/defaultLogo.png"
    
    try:
        for i in os.listdir("club_info_pages"):
            if i != ".keep" and os.path.isdir("club_info_pages/" + i):
                filepath = "club_info_pages/" + i + "/" + club_URL +  "/" + club_URL + ".json"
                if os.path.isfile(filepath):
                    club_repo_info = load_data_file(filepath)
                    if club_repo_info["Metadata"]["Published"].lower() == "yes" and club_repo_info["Metadata"]["URL"] == club_URL:
                        image_filepath = "club_info_pages/" + club_repo_info["Metadata"]["Category"].replace(" ", "_").lower() + "/" + club_repo_info["Metadata"]["URL"].replace(" ", "_").lower() + "/" + image_file_name + ".webp";
                        if os.path.isfile(image_filepath):
                            return image_filepath;
        return defaultLogo
    except:
        traceback.print_exc()
        return defaultLogo
    

@app.get("/static_image/{image_file_path:path}", response_class=FileResponse)
def retrieve_static_image(image_file_path : str):
    '''retrieves a single image from within the static_data directory, if available. Relative to the static_data folder'''

    defaultLogo = "static_data/defaultLogo.png"
    
    try:
        filepath = "static_data/" + image_file_path
        if os.path.isfile(filepath):
            return filepath
                
        return defaultLogo
    except:
        traceback.print_exc()
        return defaultLogo
    
@app.get("/repo_category_list")
def get_repo_category_list():
    '''Retrieves each club repo page's metadata including Name, Category, and URL.
    If the club repo is set to not be published, then it won't be returned.
    If the club repo is set to not be listed, then it will be returned, along with its listed status.'''
    try:
        categoryData = load_data_file("static_data/categoryInfo.json")
        return categoryData
    except:
        traceback.print_exc()
        return "none"
    
@app.get("/cafeteria_menu")
def get_testing():
    try:
        cafeteriaData = load_data_file("data/gforms_output_data.json")
        if cafeteriaData["cafeteria_data"] == {}:
            return "none"
        return cafeteriaData["cafeteria_data"]
    except:
        traceback.print_exc()
        return "none"