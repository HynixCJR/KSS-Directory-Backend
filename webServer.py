from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json
from FileHelper import *
import glob
import os, traceback
app = FastAPI()
from fastapi.responses import FileResponse

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

# HTTP get request for an announcement JSON file at specified date
@app.get("/ance/date/{date}")
def getAnce(date: str):
    return openAnce.date(date)

# HTTP request for a batch of JSON files at a specified index.
@app.get("/ance/batch/{num}/{index}")
def getAnceBatch(num: int, index: int):
    # takes in index with start point of 0
    return openAnce.batch(num, index)


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

    supervisors = []
    for supervisorID, supervisorData in repoData["Basic_Info"]["Supervisors"].items():
        supervisors.append(supervisorData)
    if supervisors != []:
        clubInfo["Supervisor(s)"] = supervisors

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
        # for categoryName, category in get_club_repo_list_data().items():
        #     for clubName, clubData in category.items():
        #         print(clubData["Tag"])
        #         if clubData["Tag"] == pingID:
        #             clubInfoProcessed = formatClubRepoAsInfo(clubData["URL"])
        #             break
        
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
    for i in os.listdir("club_info_pages"):
        if i != ".keep" and os.path.isdir("club_info_pages/" + i):
            filepath = "club_info_pages/" + i + "/" + club_URL +  "/" + club_URL + ".json"
            if os.path.isfile(filepath):
                club_repo_info = load_data_file(filepath)
                if club_repo_info["Metadata"]["Published"].lower() == "yes" and club_repo_info["Metadata"]["URL"] == club_URL:
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
    for club in clubListData.values():
        if club["Published"].lower() == "yes":
            if club["Category"] not in returned_data:
                returned_data[club["Category"]] = {club["Club_Name"]: club}
            else:
                returned_data[club["Category"]][club["Club_Name"]] = club

    return returned_data

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
def retrieve_specific_club_images(club_URL: str, image_file_name):
    '''retrieves a single image from within the club_info_pages directory, if they are available.'''

    defaultLogo = "data/defaultLogo.png"
    
    try:
        for i in os.listdir("club_info_pages"):
            if i != ".keep" and os.path.isdir("club_info_pages/" + i):
                filepath = "club_info_pages/" + i + "/" + club_URL +  "/" + club_URL + ".json"
                if os.path.isfile(filepath):
                    club_repo_info = load_data_file(filepath)
                    if club_repo_info["Metadata"]["Published"].lower() == "yes" and club_repo_info["Metadata"]["URL"] == club_URL:
                        image_filepath = "club_info_pages/" + club_repo_info["Metadata"]["Category"].replace(" ", "_").lower() + "/" + club_repo_info["Metadata"]["URL"].replace(" ", "_").lower() + "/" + image_file_name + ".png";
                        if os.path.isfile(image_filepath):
                            return image_filepath;
        return defaultLogo
    except:
        traceback.print_exc()
        return defaultLogo