from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json
import ast
import glob
import os
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
            anceData = open("announcements/" + date + ".json", "r+")
            ance = anceData.read(encoding='utf-8')
            return json.loads(ance)
        except:
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
                anceData = open(all_ance[i-1], "r+", encoding='utf-8')
                ance = json.loads(anceData.read())
                print(type(ance))
                
                clubColourDataRaw = json.loads(open("pings.json", "r+").read())
                clubColourData = {}
                for [key, value] in clubColourDataRaw.items():
                    clubColourData[value[0]] = value[2]
                for [key, value] in ance.items():
                    if key != "0":
                        if value[1] in clubColourData:
                            ance[key].append(clubColourData[value[1]])
                        else:
                            ance[key].append("none")
                print(ance)

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



@app.get("/clubinfo/{club}")
# Does not accept spaces, so spaces have to be changed to "$"
def getClubInfo(club: str):
    # Gets the info of a specific club/event, returns as dictionary
    try:
        clubInfoRawFile = open("clubInfo.json", "r+")
        clubInfoRaw = json.loads(clubInfoRawFile.read())
        clubInfoProcessed = {}
        print("0:", clubInfoRaw)
        
        for clubKey, clubValue in clubInfoRaw.items():
            keyList = ast.literal_eval(clubKey)
            if keyList[0] == club:
                if keyList[1] == "Socials":
                    socialsList = []
                    previousIter = 0
                    for i in range(len(clubValue)):
                        if clubValue[i] == ",":
                            socialsList.append(clubValue[previousIter:i])
                            print(clubValue[previousIter:i])
                            previousIter = i + 2
                        elif i == len(clubValue) - 1:
                            socialsList.append(clubValue[previousIter:i + 1])
                    clubInfoProcessed[keyList[1]] = socialsList
                else:
                    clubInfoProcessed[keyList[1]] = clubValue

            print("1:", keyList[0])

        clubColourData = open("pings.json", "r+")
        for clubColourKey, clubColourValue in json.loads(clubColourData.read()).items():
            if clubColourValue[0] == club:
                print("2:", clubColourValue)
                clubInfoProcessed["Colour"] = clubColourValue[2]
                break
        if len(clubInfoProcessed) > 0:
            print("3:", clubInfoProcessed)
            return clubInfoProcessed
        else:
            return "none"
    except:
        return "none"

@app.get("/specific_club_repo/{club_URL}")
def get_specific_club_repo_info(club_URL:str):
    '''Retrieves the info for a specific club repository page.
    Images are not included; they must be retrieved from a separate get request.
    Does not return if club is not published.
    Listed status does not affect whether the page can be returned or not.'''
    try:
        for i in os.listdir("club_info_pages"):
            for k in os.listdir("club_info_pages/" + i):
                club_repo_info_raw_file = open("club_info_pages/" + i + "/" + k +  "/" + k + ".json", "r+")
                club_repo_info = json.loads(club_repo_info_raw_file.read())
                if club_repo_info["Metadata"]["Published"].lower() == "yes" and club_repo_info["Metadata"]["URL"] == club_URL:
                    return club_repo_info
        else:
            return "none"
    except:
        return "none"

@app.get("/club_repo_main")
def get_club_repo_main():
    '''Retrieves every single club info page, excluding images.
    This runs on build time for the landing club repo page.'''
    returned_list = []
    for i in os.listdir("club_info_pages"):
        for k in os.listdir("club_info_pages/" + i):
            club_repo_info_raw_file = open("club_info_pages/" + i + "/" + k + "/" + k + ".json", "r+")
            club_repo_info = json.loads(club_repo_info_raw_file.read())
            if club_repo_info["Metadata"]["Published"].lower() == "yes":
                returned_list.append({"URL": club_repo_info["Metadata"]["URL"], "Content": club_repo_info})
    return returned_list

@app.get("/club_repo_list")
def get_club_repo_list():
    '''Retrieves each club repo page's metadata including Name, Category, and URL.
    If the club repo is set to not be published, then it won't be returned.
    If the club repo is set to not be listed, then it will be returned, along with its listed status.'''
    try:
        returned_file = {}
        for i in os.listdir("club_info_pages"):
            for k in os.listdir("club_info_pages/" + i):
                club_repo_info_raw_file = open("club_info_pages/" + i + "/" + k + "/" + k + ".json", "r+")
                club_repo_info = json.loads(club_repo_info_raw_file.read())
                if club_repo_info["Metadata"]["Published"].lower() == "yes":
                    if club_repo_info["Metadata"]["Category"] not in returned_file:
                        returned_file[club_repo_info["Metadata"]["Category"]] = {
                            club_repo_info["Metadata"]["Club_Name"]: {
                                "Club_Name": club_repo_info["Metadata"]["Club_Name"],
                                "URL": club_repo_info["Metadata"]["URL"],
                                "Listed": club_repo_info["Metadata"]["Listed"]}}
                    else:
                        returned_file[club_repo_info["Metadata"]["Category"]][club_repo_info["Metadata"]["Club_Name"]] = {
                            "Club_Name": club_repo_info["Metadata"]["Club_Name"],
                            "URL": club_repo_info["Metadata"]["URL"],
                            "Listed": club_repo_info["Metadata"]["Listed"]}
        return returned_file
    except:
        return "none"

@app.get("/specific_club_images/{club_URL}/{image_file_name}", response_class=FileResponse)
def retrieve_specific_club_images(club_URL: str, image_file_name):
    '''retrieves a single image from within the club_info_pages directory, if they are available.'''
    try:
        for i in os.listdir("club_info_pages"):
            for k in os.listdir("club_info_pages/" + i):
                club_repo_info_raw_file = open("club_info_pages/" + i.replace(" ", "_") + "/" + k.replace(" ", "_").lower() +  "/" + k.replace(" ", "_").lower() + ".json", "r+")
                club_repo_info = json.loads(club_repo_info_raw_file.read())
                if club_repo_info["Metadata"]["Published"].lower() == "yes" and club_repo_info["Metadata"]["URL"] == club_URL:
                    
                    return "club_info_pages/" + club_repo_info["Metadata"]["Category"].replace(" ", "_").lower() + "/" + club_repo_info["Metadata"]["Club_Name"].replace(" ", "_").lower() + "/" + image_file_name + ".png"
        else:
            return "none"
    except:
        return "none"