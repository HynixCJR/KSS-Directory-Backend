# File exists to hold all the parsing specific functions of the gdocs retreiver, 
# so that the logic for auth / other stuff can be separated from the ridiculously long parsing functions

import os
import json
import requests
import traceback
from PIL import Image

from FileHelper import *

def retrieve_and_save_img(img_url:str, img_file_name:str, img_file_path:str, old_hash:str):
    '''saves an image from a link, with the given file name and path, returns the current raw file hash'''
    if not os.path.exists(img_file_path + "/raw"):
        os.makedirs(img_file_path + "/raw")
    
    rawFilepath = img_file_path + "/raw/" + img_file_name + ".png"
    optimisedFilepath = img_file_path + "/" + img_file_name + ".webp"
    
    print("-> Saving Image: " + str(img_file_name))
    #print("Old Hash: " + old_hash)
    
    try:
        img_data = requests.get(img_url).content

        with open(rawFilepath, 'wb') as handler:
            handler.write(img_data)

        raw_file_hash = hash_file(rawFilepath)
        #print("New Hash: " + raw_file_hash)

        if old_hash != raw_file_hash:
            if raw_file_hash != "none":
                # Convert to webp to save bandwidth
                with Image.open(rawFilepath) as image:
                    image.save(optimisedFilepath)

                print("Finished Saving Updated Image.")
                return raw_file_hash
            else:
                print("Error saving image " + img_file_name + ". Failed hashing newly downloaded file. Something is broken.")
        else:
            print("Ignoring Unchanged Image.")
    except:
        traceback.print_exc()



    return old_hash

def format_dates_properly(month:str, date, year, time):
    '''Takes in a month, date, year, and time, and outputs a consistently formatted (ISO) version. I hate this so much.'''

    months = {'01': ['january', 'jan', '01', '1', 'janaury'],
            '02': ['february', 'feb', '02', '2', 'febuary', 'febraury'],
            '03': ['march', 'mar', '03', '3'],
            '04': ['april', 'apr', '04', '4', 'apirl'],
            '05': ['may', '05', '5'],
            '06': ['june', '06', '6', 'jun'],
            '07': ['july', '07', '7', 'jul'],
            '08': ['august', 'auguest', '08', '8', 'aug'],
            '09': ['september', 'septmeber', '09', '9', 'sept'],
            '10': ['october', 'octobre', 'oct', '10'],
            '11': ['november', 'novembre', 'novmeber', '11', 'nov'],
            '12': ['december', 'decembre', 'dec', '12']
            }
    
    max_days_per_month = {
        '01': 31,
        '02': 28, # account for leap years separately
        '03': 31,
        '04': 30,
        '05': 31,
        '06': 30,
        '07': 31,
        '08': 31,
        '09': 30,
        '10': 31,
        '11': 30,
        '12': 31
    }
    date_formatted = ""

    # FORMAT YEAR

    year_only_num = ""
    for i in year.replace("\n", "").replace(" ", ""):
        if i in ['0','1','2','3','4','5','6','7','8','9']:
            # makes sure that there are no letters in the year.
            # there's probably a better way of doing this.
            # there's definitely a better way of doing this.
            year_only_num += i
    try:
        if len(str(year_only_num)) == 4 and int(year_only_num):
            # if year given is actually 4 char long (i.e., 20xx) and can be converted to an integer (i.e., it is an actual year), then append to date_formatted.
            date_formatted += str(year_only_num)
        else:
            # if not, then return error.
            return "error"
    except:
        # if int(year) is unsuccessful, return error as well.
        return "error"


    # FORMAT MONTH

    for month_iso, month_unformatted in months.items():
        # check if the specified month is in the months dict, then append the month in iso format to date_formatted
        if month.lower().replace("\n", "").replace(" ", "") in month_unformatted:
            date_formatted += "-" + month_iso
            break
    if len(date_formatted) < 7:
        # if there were no matches for month, e.g. if spelling was incorrect, then return an error
        return "error"


    # FORMAT DATE

    date = str(date).replace(" ", "").replace("\n", "")
    date_only_num = ""
    for i in date:
        if i in ['0','1','2','3','4','5','6','7','8','9']:
            # makes sure that there are no letters in the date.
            # there's probably a better way of doing this.
            # there's definitely a better way of doing this.
            date_only_num += (i)

    date_valid = False
    if int(year_only_num) % 4 == 0 and month_iso == "02" and int(date_only_num) <= 29 or int(year_only_num) % 4 == 0 and int(date_only_num) <= max_days_per_month[month_iso]:
        # checking if the date is valid, given the month (february) in a leap year, or if it's any other unaffected month.
        date_valid = True
    elif int(year_only_num) % 4 != 0 and int(date_only_num) <= max_days_per_month[month_iso]:
        # checking if the date is valid, given the month in a non leap year.
        date_valid = True
    else:
        return "error"


    if len(date_only_num) == 2:
        # if length of date_only_num is correct, then append that value to the date_formatted.
        date_formatted += "-" + date_only_num
    elif len(date_only_num) == 1:
        date_formatted += "-0" + date_only_num
    else:
        return "error"
    

    # FORMAT TIME

    time = time.replace(" ","").replace("\n", "").lower()
    if ":" in time:
        # if the time uses "3:00 PM" or "15:00" formatting instead of just "3 PM"

        try:
            # checks if there are only numbers and a colon, i.e. if there is no "PM" or "AM" included
            if time[0] == '0':
                a = int(time[1:].replace(":", ""))
            else:
                a = int(time.replace(":", ""))
            if len(time) == 5 and time[2] == ":":
                if time[3] != "0" and int(time[3:]) < 60 or time[3] == "0":
                    # if the time is something like "11:13" and the minutes are actually valid
                    if time[0] == "0" or int(time[0:2]) < 24:
                        # if the hour starts with 0, e.g. "08:30"
                        # or if the hour is less than 24, e.g. "23:59"
                        date_formatted += ("T" + time)
                    else:
                        return "error"
            elif len(time) == 4 and time[1] == ":":
                # if the hour is only one char, and the minutes are actually valid. e.g. "3:00"

                if time[2] != "0" and int(time[2:]) < 60 or time[2] == "0":
                    date_formatted += ("T0" + time)
            else:
                return "error"
        except:
            # if there are characters other than colon and numbers, i.e. if there is "AM" or "PM" included.
            
            if len(time) == 7 and time[2] == ":" and time[5:] in ['pm', 'am']:
                # if hours is two char, minutes are listed and valid, and pm/am is specified.
                # e.g. "03:23 PM" or "12:44 AM", though capitalization and spaces are removed.

                if time[3] != "0" and int(time[3:5]) < 60 or time[3] == "0":
                    if time[0] == "0":
                        # if the hour begins with 0, e.g. "04:30 PM"
                        if time[5:] == "pm" and time[1] != "0":
                            # if the hour begins with 0, isn't "00", and is PM, add 12 to the second char and append.
                            date_formatted += ("T" + str(int(time[1]) + 12) + time[2:5])
                        elif time[5:] == "am" and time[1] != "0":
                            # if the hour begins with 0, isn't "00", and is AM, append directly.
                            date_formatted += ("T" + time[0:5])
                        else:
                            # if the hour is "00", then it isn't valid. therefore, produce an error.
                            return "error"
                    elif time[0] == "1" and int(time[0:2]) < 13:
                        # if the hour is double digits, and is less than 13.
                        if time[0:2] == "12":
                            # 12 AM/PM edgecase, because the person who designed times is genuinely braindead.
                            if time[5:] == "am":
                                # 12:XX AM = 00XX in ISO, i.e. midnight
                                date_formatted += ("T00:" + time[3:5])
                            elif time[5:] == "pm":
                                # 12:XX PM = 12XX in ISO, i.e. lunchtime
                                date_formatted += ("T" + time[0:5])
                        else:
                            # if the hour is 10 or 11
                            if time[5:] == "am":
                                date_formatted += ("T" + time[0:5])
                            elif time[5:] == "pm":
                                date_formatted += ("T" + str(12 + int(time[0:2])) + time[2:5])
                    else:
                        # if the hour is greater than 12, and includes PM/AM, throw an error
                        # e.g. "15:30 PM"
                        return "error"
                else:
                    return "error"
            elif len(time) == 6 and time[1] == ":" and time[4:] in ['pm', 'am']:
                # if hours is only one char, minutes are listed and valid, and pm/am is specified

                if time[2] != "0" and int(time[2:4]) < 60 or time[2] == "0":
                    if time[4:] == 'pm':
                        date_formatted += ("T" + str(int(time[0]) + 12) + time[1:4])
                    elif time[4:] == 'am':
                        date_formatted += ("T0" + time[0:4])
            else:
                return "error"

    else:
        # if the time doesn't use ":"

        try:
            # checks if there are only numbers and a colon, i.e. if there is no "PM" or "AM" included.
            # this edge case is horrendous, and should not be valid, but idgaf because someone is literally just going to put "3" and complain that it didn't work.
            if time[0] == '0':
                a = int(time[1:])
            else:
                a = int(time)

            if 2 < len(time) < 5:
                # if there are minutes listed, but not separated by a colon and without AM/PM, e.g. "0312" or "830"
                
                if time[0] == '0' and len(time) == 4 or int(time[0:2]) < 24 and len(time) == 4:
                    if time[2] != "0" and int(time[2:]) < 60 or time[2] == "0":
                        # e.g. "0830" or "1259"
                        date_formatted += ("T" + time[0:2] + ":" + time[2:])
                    else:
                        return "error"
                elif time[0] != '0' and len(time) == 3:
                    # e.g. "830"
                    if time[1] != '0' and int(time[1:]) < 60 or time[1] == "0":
                        date_formatted += ("T0" + time[0] + ":" + time[1:])
                    else:
                        return "error"
                else:
                    return "error"
            elif len(time) < 3:
                # if there are no minutes nor PM/AM listed, just the hour. e.g. "11"
                if len(time) == 2 and time[0] == "0" or len(time) == 2 and int(time) < 24:
                    # if the time is two characters long, e.g. "03" or "11".
                    date_formatted += ("T" + time + ":00")
                elif len(time) == 1:
                    # if the time is one character long, e.g. "8".
                    # this defaults to being in the morning, which may be problematic if someone puts "4" and expects it to mean 4 PM.
                    # that's on them though.
                    date_formatted += ("T0" + time + ":00")
                else:
                    return "error"
            else:
                return "error"
        except:
            # if there are characters other than colon and numbers, i.e. if there is "AM" or "PM" included.
            # e.g. "1230 PM" or "3 PM"
            if 4 < len(time) < 7:
                # if minutes are included
                
                if len(time) == 6 and time[4:] in ['am', 'pm']:
                    # if the hour is two char long
                    if time[0] == "0" and time[2] != "0" and int(time[2:4]) < 60 or time[0] == "0" and time[2] == "0":
                        # edgecase where for some reason the user puts "0300 PM"
                        if time[4:] == "am":
                            date_formatted += ("T" + time[0:2] + ":" + time[2:4])
                        elif time[4:] == "pm":
                            date_formatted += ("T" + str(int(time[1]) + 12) + ":" + time[2:4])
                        else:
                            return "error"
                    elif time[0] == "1" and time[2] != "0" and int(time[2:4]) < 60 and int(time[0:2]) < 13 or time[0] == "1" and time[2] == "0" and int(time[0:2]) < 13:
                        # if the hour is 10, 11, or 12.
                        # doesn't include hours of 13 or higher, since 13 PM is not valid.
                        if time[0:2] == "12":
                            if time[4:] == 'am':
                                # 12XX AM = 00XX in ISO, i.e. midnight
                                date_formatted += ("T00:" + time[2:4])
                            elif time[4:] == 'pm':
                                # 12XX PM = 12XX in ISO, i.e. lunchtime
                                date_formatted += ("T" + time[0:2] + ":" + time[2:4])
                            else:
                                return "error"
                        else:
                            if time[4:] == "am":
                                date_formatted += ("T" + time[0:2] + ":" + time[2:4])
                            elif time[4:] == "pm":
                                date_formatted += ("T" + str(int(time[0:3]) + 12) + ":" + time[3:5])
                            else:
                                return "error"
                    else:
                        return "error"
                elif len(time) == 5 and time[3:] in ['am', 'pm']:
                    # if the hour is one char long, e.g. "330 PM"
                    if time[1] != "0" and int(time[1:3]) < 60 or time[1] == "0":
                        if time[3:] == 'am':
                            date_formatted += ("T0" + time[0] + ":" + time[1:3])
                        elif time[3:] == 'pm':
                            date_formatted += ("T" + str(int(time[0]) + 12) + ":" + time[1:3])
                        else:
                            return "error"
                else:
                    return "error"
            elif len(time) < 5:
                # e.g. if the time is written as "03 PM", "12 PM", or "3 PM"
                if len(time) == 4 and time[2:] in ['am', 'pm']:
                    # if the hour has two chars
                    if time[0] == "0" and time[1] != "0":
                        # if hour is 1-9
                        if time[2:] == 'am':
                            date_formatted += ("T" + time[0:2] + ":00")
                        elif time[2:] == 'pm':
                            date_formatted += ("T" + str(int(time[1]) + 12) + ":00")
                    elif time[0] == "1" and int(time[0:2]) < 13:
                        # if hour is 10, 11, or 12.
                        # excludes hours above 12 since those don't make sense with AM/PM.
                        if time[1] == "2":
                            if time[3:] == 'am':
                                # 12 AM = 00 in ISO, i.e. midnight
                                date_formatted += ("T00:00")
                            elif time[3:] == 'pm':
                                # 12 PM = 12 in ISO, i.e. lunchtime
                                date_formatted += ("T12:00")
                    else:
                        return "error"

                elif len(time) == 3 and time[1:] in ['am', 'pm']:
                    # if the hour only has one char
                    if time[1:] == 'am':
                        date_formatted += ("-0" + time[0] + ":00")
                    elif time[1:] == 'pm':
                        date_formatted += ("T" + str(int(time[0]) + 12) + ":00")
                else:
                    return "error"
    if len(date_formatted) != 16:
        # one final check to make sure everything appended properly
        return "error"
    return date_formatted

def format_yes_or_no_properly(content:str):
    yes = ["yes", "ye", "y", "yeah", "yea", "yep"]
    no = ["no", "n", "nah", "nope", "nop", "na", "n/a"]
    if content in yes:
        return True
    elif content in no:
        return False
    else:
        return "error"
        
def dump_to_json(path: str, file_name:str, content):
        '''dumps content to a json file at a specified path. if the path/file don't already exist, the function creates it.'''
        if not os.path.exists(path):
            os.makedirs(path)
        try:
            # Opening json, if it exists
            jsonFile = open(path + "/" + file_name + ".json", "r+")
            # removes all stuff in json from 0th position
            jsonFile.truncate(0)
            # moves cursor back to 0th position
            jsonFile.seek(0)
        except:
            jsonFile = open(path + "/" + file_name + ".json", "w")
            # Writing the date information (the dictionary) to the newly created file

        if type(content) == dict:
            jsonFile.write(json.dumps(content))
        else:
            jsonFile.write(json.dumps({0:content}))
            # written to json file as a new dictionary with 0th key to account for values that aren't dictionaries.
            # for some reason the google docs api returns a list, not a dictionary?? so this accounts for that.

        jsonFile.flush()


def parse_stupid_text(elementArray):
    '''For some reason some textruns are separated into different elements??? Why.'''
    
    outputString = ""
    for element in elementArray:
        outputString += element["textRun"]["content"]

    return outputString

def scrape_doc(full_doc, doc_images, doc_modified_time, categories, old_image_data):
    '''the full doc scraping function'''

    club_discord_tag = ""
    club_directory_path = ""
    club_url = ""

    # dump_data_file(full_doc, "crap.json")

    club_data = {}

    for index, line in enumerate(full_doc):
        if "paragraph" in line and line["paragraph"]["paragraphStyle"]["namedStyleType"] == "HEADING_1":
            # Dividing the parsing by if they've got the heading applied

            if line["paragraph"]["elements"][0]["textRun"]["content"] == "Metadata\n":
                # Detects when the metadata section is reached.

                club_data = {"Metadata": {"Last_modified": doc_modified_time}}

                for k in range(10):
                    if "table" in full_doc[index + k]:
                        # detects if line is a table

                        for j in full_doc[index + k]["table"]["tableRows"]:
                            # iterates through each row in table

                            table_row_first_cell = j["tableCells"][0]["content"][0]["paragraph"]["elements"][0]["textRun"]["content"].replace("\n", "").lower()
                            table_row_second_cell = j["tableCells"][1]["content"][0]["paragraph"]["elements"][0]["textRun"]["content"].replace("\n", "")

                            if table_row_first_cell == "info page version":
                                club_data["Metadata"]["Info_Page_Ver"] = float(table_row_second_cell)
                            elif table_row_first_cell == "tag":
                                club_data["Metadata"]["Tag"] = table_row_second_cell.replace("\n", "").replace(" ", "")
                            elif table_row_first_cell == "club name":
                                club_data["Metadata"]["Club_Name"] = table_row_second_cell
                            elif table_row_first_cell == "category":
                                club_data["Metadata"]["Category"] = table_row_second_cell
                            elif table_row_first_cell == "url":
                                club_data["Metadata"]["URL"] = table_row_second_cell
                            elif table_row_first_cell == "listed":
                                club_data["Metadata"]["Listed"] = table_row_second_cell
                            elif table_row_first_cell == "published":
                                club_data["Metadata"]["Published"] = table_row_second_cell
                            elif table_row_first_cell == "claimed":
                                club_data["Metadata"]["Claimed"] = table_row_second_cell
                            else:
                                break
                        
                # handle missing category
                if club_data["Metadata"]["Category"] == "":
                    club_data["Metadata"]["Category"] = "Other Clubs"

                # handle no matching category
                if club_data["Metadata"]["Category"].replace(" ", "_").lower() not in categories:
                    print("Invalid Category. Moving To Other Clubs.")
                    club_data["Metadata"]["Category"] = "Other Clubs"

                club_discord_tag = club_data["Metadata"]["Tag"].replace("\n", "").replace(" ", "")
                club_url = club_data["Metadata"]["URL"].replace(" ", "_")
                club_directory_path = "club_info_pages/" + club_data["Metadata"]["Category"].replace(" ", "_").lower() + "/" + club_data["Metadata"]["URL"].replace(" ", "_").lower()
    
            elif line["paragraph"]["elements"][0]["textRun"]["content"] == "Basic Info":
                # detects when the Basic Info section is reached.

                club_data["Basic_Info"] = {}

                for k in range(10):
                    if "table" in full_doc[index + k]:
                        # detects if line is a table
                        table_column = full_doc[index + k]["table"]["tableRows"][0]["tableCells"]
                        if table_column[0]["content"][0]["paragraph"]["elements"][0]["textRun"]["content"].replace("\n", "") == "Club/EC description":
                            # if table is the description section
                            # Note: this is pain.
                            
                            if len(table_column[1]["content"][0]["paragraph"]["elements"][0]["textRun"]["content"]) > 1:
                                club_data["Basic_Info"]["Description"] = table_column[1]["content"][0]["paragraph"]["elements"][0]["textRun"]["content"]
                            else:
                                #TODO: make sure this matches up with how the "no description" scenario is set up currently.
                                club_data["Basic_Info"]["Description"] = "No description added yet. Please contact the KSS Directory Maintainers on our Discord Server to see if one can be added! Thanks :)"

                        elif table_column[0]["content"][0]["paragraph"]["elements"][0]["textRun"]["content"].replace("\n", "") == "Currently running/active?":
                            # if table is the activity section

                            yes_answer = ["yes", "yes.", "yep", "yeah", "yea", "y", "ye", '"yes"']
                            no_answer = ["no", "no.", "nope", "nah", "n", "no", '"no"']
                            if table_column[1]["content"][0]["paragraph"]["elements"][0]["textRun"]["content"].lower().replace(" ", "").replace("\n", "") in yes_answer:
                                # if club is currently active
                                club_data["Basic_Info"]["Activity"] = "Yes"
                            elif table_column[1]["content"][0]["paragraph"]["elements"][0]["textRun"]["content"].lower().replace(" ", "").replace("\n", "") in no_answer:
                                # if club isn't currently active
                                club_data["Basic_Info"]["Activity"] = "No"
                            else:
                                # if exec user doesn't fill out this section, or if they use some unorthodox version of 'yes' or 'no'.
                                club_data["Basic_Info"]["Activity"] = "Unspecified"

                        elif table_column[0]["content"][0]["paragraph"]["elements"][0]["textRun"]["content"].replace("\n", "") == "Supervisor(s)":
                            # if table is the supervisors section

                            if len(full_doc[index + k]["table"]["tableRows"][1]["tableCells"][0]["content"][0]["paragraph"]["elements"][0]["textRun"]["content"]) < 5:
                                # if the first row has no supervisor listed, set  supervisor(s) key to "unspecified" value
                                club_data["Basic_Info"]["Supervisors"] = "Unspecified"
                            else:
                                # if the first row has something in it, set supervisor(s) key to an actual dict
                                club_data["Basic_Info"]["Supervisors"] = {}

                            for row_index, row in enumerate(full_doc[index + k]["table"]["tableRows"]):
                                # iterating through all the rows of the supervisor(s) google doc table

                                if club_data["Basic_Info"]["Supervisors"] == "Unspecified":
                                    break

                                elif row["tableCells"][0]["content"][0]["paragraph"]["elements"][0]["textRun"]["content"].replace("\n", "") != "Supervisor(s)" and len(row["tableCells"][0]["content"][0]["paragraph"]["elements"][0]["textRun"]["content"]) > 5:
                                    # if there is an actual supervisor listed, assign their name to a value with its index as the key in the supervisor(s) dict
                                    # pain
                                    club_data["Basic_Info"]["Supervisors"][row_index] = row["tableCells"][0]["content"][0]["paragraph"]["elements"][0]["textRun"]["content"].replace("\n", "")

            elif line["paragraph"]["elements"][0]["textRun"]["content"].replace("\n", "") == "Weekly Meeting Times":
                # detects when the weekly meeting times section has been reached

                club_data["Meeting_Times"] = {}

                for k in range(10):
                    if "table" in full_doc[index + k]:
                        # detects if line is a table
                        for table_row_index, table_row in enumerate(full_doc[index + k]["table"]["tableRows"]):
                            # iterate through each row in the table
                            if table_row["tableCells"][0]["content"][0]["paragraph"]["elements"][0]["textRun"]["content"].replace("\n", "") != "Meeting title":
                                # if table row is the header area, don't do anything with it.

                                days_of_the_week = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

                                # i hate this so much
                                meeting_title = table_row["tableCells"][0]["content"][0]["paragraph"]["elements"][0]["textRun"]["content"].replace("\n", "")
                                meeting_day = table_row["tableCells"][1]["content"][0]["paragraph"]["elements"][0]["textRun"]["content"].replace("\n", "").lower().replace(" ", "")
                                meeting_start_time_unverified = table_row["tableCells"][2]["content"][0]["paragraph"]["elements"][0]["textRun"]["content"].replace("\n", "").lower().replace(" ", "")
                                meeting_end_time_unverified = table_row["tableCells"][3]["content"][0]["paragraph"]["elements"][0]["textRun"]["content"].replace("\n", "").lower().replace(" ", "")
                                meeting_location = parse_stupid_text(table_row["tableCells"][4]["content"][0]["paragraph"]["elements"]).replace("\n", "")
                                

                                
                                if meeting_day in days_of_the_week and len(meeting_start_time_unverified) > 5 and len(meeting_location) > 1:
                                    # checking if there's anything actually in the required fields

                                    def meeting_time_check(time):
                                        if 0 < int(time[0]) <= 9 and time[1] == ":" and 0 <= int(time[2]) <= 5 and 0 <= int(time[3]) <= 9:
                                            # if the hour is single digits

                                            # store the time in ISO 8601 format
                                            if time[4:6] == "pm":
                                                # add 12 to the hour if it's PM
                                                return str(12 + int(time[0])) + time[1:4]

                                            elif time[4:6] == "am":
                                                # set it straight up if it's AM
                                                return "0" + time[0:4]

                                        elif time[0] == "1" and 0 <= int(time[1]) <= 2 and time[2] == ":" and 0 <= int(time[3]) <= 5 and 0 <= int(time[4]) <= 9:
                                            # if the hour is double digits

                                            # store the time in ISO 8601 format
                                            if time[5:7] == "pm":
                                                # add 12 to the hour if it's PM
                                                if time[1] != "2":
                                                    return str(12 + int(time[0])) + time[2:5]
                                                else:
                                                    # 12 PM exception
                                                    return time[0:5]

                                            elif time[5:7] == "am":
                                                # set it straight up if it's AM
                                                if time[1] != "2":
                                                    return time[0:5]
                                                else:
                                                    # 12 AM exception
                                                    return "00" + time[2:5]

                                        else:
                                            return "not_verified!"

                                    meeting_start_time = meeting_time_check(meeting_start_time_unverified)
                                    if meeting_start_time == "not_verified!":
                                        break
                                    else:
                                        club_meeting = {}

                                        if len(meeting_title) > 1:
                                            # meeting title
                                            club_meeting["Meeting_Title"] = meeting_title
                                        
                                        club_meeting["Meeting_Day"] = meeting_day
                                        # meeting day
                                        
                                        club_meeting["Meeting_Start_Time"] = meeting_start_time
                                        # meeting start time
                                        if len(meeting_end_time_unverified) > 5:
                                            meeting_end_time = meeting_time_check(meeting_end_time_unverified)
                                            # meeting end time
                                            # since it's not required, I don't have to void the entire meeting time if if the end time isn't valid
                                            if meeting_end_time != "unverified":
                                                club_meeting["Meeting_End_Time"] = meeting_end_time
                                        
                                        club_meeting["Meeting_Location"] = meeting_location
 
                                        club_data["Meeting_Times"][table_row_index] = club_meeting
                        
            elif line["paragraph"]["elements"][0]["textRun"]["content"].replace("\n", "") == "Links":
                # detects when the links section has been reached

                club_data["Links"] = {}

                for k in range(10):
                    if "table" in full_doc[index + k]:
                        # detects if line is a table
                        for table_row_index, table_row in enumerate(full_doc[index + k]["table"]["tableRows"]):

                            if table_row["tableCells"][0]["content"][0]["paragraph"]["elements"][0]["textRun"]["content"].replace("\n", "").lower() != "link name":
                                # if table row is the header area, don't do anything with it.

                                if "link" in table_row["tableCells"][1]["content"][0]["paragraph"]["elements"][0]["textRun"]["textStyle"]:
                                    # if the listed link is actually a valid URL (i put this if statement on another line because i don't want to scroll horizontally to debug the code)
                                    if table_row["tableCells"][0]["content"][0]["paragraph"]["elements"][0]["textRun"]["content"] != "\n":
                                        # if there is actually a name associated with the link, set that as the link's name.
                                        link_name = table_row["tableCells"][0]["content"][0]["paragraph"]["elements"][0]["textRun"]["content"].replace("\n", "")
                                    else:
                                        # if there is no name associated with the link, set the link's name to "none"
                                        link_name = "none"
                                    link_url = table_row["tableCells"][1]["content"][0]["paragraph"]["elements"][0]["textRun"]["textStyle"]["link"]["url"]
                                    club_data["Links"][table_row_index] = [link_name, link_url]
                    
            elif line["paragraph"]["elements"][0]["textRun"]["content"].replace("\n", "") == "Logo" or line["paragraph"]["elements"][0]["textRun"]["content"].replace("\n", "") == "Banner":
                # detects when the logo or banner sections have been reached.
                # they're bunched together because the parsing behaviour is the same, as they both have the same table format.

                if "Images" not in club_data:
                    club_data["Images"] = {}

                if not os.path.exists(club_directory_path):
                    # if the folder for this club doesn't already exist, this makes a new one for it.
                    os.makedirs(club_directory_path)
                
                for k in range(10):
                    if "table" in full_doc[index+k] and "inlineObjectElement" in full_doc[index + k]["table"]["tableRows"][0]["tableCells"][1]["content"][0]["paragraph"]["elements"][0]:
                        # detects if line is a table and if an image is in the second cell.

                        img_uri_tag = full_doc[index + k]["table"]["tableRows"][0]["tableCells"][1]["content"][0]["paragraph"]["elements"][0]["inlineObjectElement"]["inlineObjectId"]
                        # setting the uri tag to a variable so that the following line of code is more readable

                        image_title = line["paragraph"]["elements"][0]["textRun"]["content"].replace("\n", "").lower()

                        old_hash = "none"
                        if image_title in old_image_data:
                            old_hash = old_image_data[image_title]["Hash"]

                        file_hash = retrieve_and_save_img(doc_images[img_uri_tag], image_title, club_directory_path, old_hash)

                        # add a section in the dict that indicates that an image exists, which is so that the front-end knows to make another request specifically for the image
                        if file_hash != "none":
                            club_data["Images"][image_title] = {}
                            club_data["Images"][image_title]["Hash"] = file_hash
                        
            elif line["paragraph"]["elements"][0]["textRun"]["content"].replace("\n", "") == "Current Executive Members":
                # detects when the execs section has been reached.

                club_data["Execs"] = {}

                for k in range(len(full_doc) - index):
                    if "table" in full_doc[index + k]:
                        # detects if line is a table

                        for table_row_index, table_row in enumerate(full_doc[index + k]["table"]["tableRows"]):

                            if table_row["tableCells"][0]["content"][0]["paragraph"]["elements"][0]["textRun"]["content"].replace("\n", "").lower() != "name of exec":
                                # if table row is the header area, don't do anything with it.

                                if table_row["tableCells"][0]["content"][0]["paragraph"]["elements"][0]["textRun"]["content"].replace("\n", "") != "":
                                    # if there is actually a name listed in the cell.

                                    exec_name = table_row["tableCells"][0]["content"][0]["paragraph"]["elements"][0]["textRun"]["content"].replace("\n", "")

                                    if table_row["tableCells"][1]["content"][0]["paragraph"]["elements"][0]["textRun"]["content"] != "\n":
                                        # if there is actually a position associated with the exec, set that as the exec's position.
                                        exec_position = table_row["tableCells"][1]["content"][0]["paragraph"]["elements"][0]["textRun"]["content"].replace("\n", "")
                                    else:
                                        # if there is no position associated with the exec, set the exec's position to "none"
                                        exec_position = "none"
                                    club_data["Execs"][exec_name] = exec_position
                        break
            
            elif line["paragraph"]["elements"][0]["textRun"]["content"].replace("\n", "") == "Current Events":
                # detects when the execs section has been reached.

                club_data["Events"] = {}
                for j in range(len(full_doc) - index):
                    if "paragraph" in full_doc[index + j] and full_doc[index + j]["paragraph"]["elements"][0]["textRun"]["content"].replace("\n", "")[0:5] == "Event" and full_doc[index + j]["paragraph"]["paragraphStyle"]["namedStyleType"] == "HEADING_2":
                        # if the event subheading is reached.
                        
                        for k in range(7):
                            if "table" in full_doc[index + j + k] and full_doc[index + k + j]["table"]["tableRows"][0]["tableCells"][0]["content"][0]["paragraph"]["elements"][0]["textRun"]["content"].replace("\n", "") == "Publish event?":
                                # detects if line is a table, and if it's the first cell.

                                try:
                                    # if the title is formatted incorrectly, e.g. "event abc" instead of "event 2", then quit out of the loop and try the next listed event.
                                    event_label = int(full_doc[index + j]["paragraph"]["elements"][0]["textRun"]["content"].replace("\n", "").replace(" ", "")[5:])
                                except:
                                    break

                                club_data["Events"][event_label] = {}

                                for table_row_index, table_row in enumerate(full_doc[index + k + j]["table"]["tableRows"]):
                                    if table_row["tableCells"][0]["content"][0]["paragraph"]["elements"][0]["textRun"]["content"].replace("\n", "") == "Publish event?":
                                        # if table row is in the event publish status section.
                                        yes_or_no = table_row["tableCells"][1]["content"][0]["paragraph"]["elements"][0]["textRun"]["content"].replace("\n", "").replace(" ", "").lower()
                                        if format_yes_or_no_properly(yes_or_no) != "error":
                                            club_data["Events"][event_label]["Publish_Status"] = format_yes_or_no_properly(yes_or_no)
                                        else:
                                            # if there is nothing written in the cell, set the publish status to false.
                                            club_data["Events"][event_label]["publish_status"] = False
                                    elif table_row["tableCells"][0]["content"][0]["paragraph"]["elements"][0]["textRun"]["content"].replace("\n", "") == "Event Name (required)":
                                        # if table row is in event name section 
                                        if len(table_row["tableCells"][1]["content"][0]["paragraph"]["elements"][0]["textRun"]["content"].replace("\n", "").replace(" ", "")) > 2:
                                            # if the content in the adjacent cell actually exists, i.e., there is an actual name associated with the event.
                                            club_data["Events"][event_label]["Event_Name"] = table_row["tableCells"][1]["content"][0]["paragraph"]["elements"][0]["textRun"]["content"].replace("\n", "")
                                        else:
                                            # if the name does not exist, delete the key from the dictionary, and quit out of the loop.
                                            del club_data["Events"][event_label]
                                            break
                                    elif table_row["tableCells"][0]["content"][0]["paragraph"]["elements"][0]["textRun"]["content"].replace("\n", "") == "Description (required)":
                                        # if table row is in description section
                                        if len(table_row["tableCells"][1]["content"][0]["paragraph"]["elements"][0]["textRun"]["content"].replace("\n", "").replace(" ", "")) > 5:
                                            # if the description actually exists
                                            club_data["Events"][event_label]["Description"] = table_row["tableCells"][1]["content"][0]["paragraph"]["elements"][0]["textRun"]["content"]
                                        else:
                                            # if description doesn't exist, then delete the key from the dictionary
                                            del club_data["Events"][event_label]
                                    elif table_row["tableCells"][0]["content"][0]["paragraph"]["elements"][0]["textRun"]["content"].replace("\n", "") == "Signup fee":
                                        # if table row is in sign up fee section
                                        if len(table_row["tableCells"][1]["content"][0]["paragraph"]["elements"][0]["textRun"]["content"].replace("\n", "").replace(" ", "")) > 0:
                                            club_data["Events"][event_label]["Signup_Fee"] = table_row["tableCells"][1]["content"][0]["paragraph"]["elements"][0]["textRun"]["content"].replace("\n", "")
                                        else:
                                            # if the signup fee section doesn't have anything in it, set the signup fee to be "N/A"
                                            # this is preferrabl to not having the signup fee at all on the website for clarity purposes.
                                            club_data["Events"][event_label]["Signup_Fee"] = "N/A"
                                    elif table_row["tableCells"][0]["content"][0]["paragraph"]["elements"][0]["textRun"]["content"].replace("\n", "") == "Image":
                                        # if table row is in image section
                                        if "inlineObjectElement" in table_row["tableCells"][1]["content"][0]["paragraph"]["elements"][0]:
                                            # if there is actually an inline object (image) in the cell.
                                            if "Images" not in club_data:
                                                club_data["Images"] = {}
                                            img_uri_tag = table_row["tableCells"][1]["content"][0]["paragraph"]["elements"][0]["inlineObjectElement"]["inlineObjectId"]
                                            if not os.path.exists(club_directory_path):
                                                # if the folder for this club doesn't already exist, this makes a new one for it.
                                                os.makedirs(club_directory_path)

                                            image_title = "Event_" + str(event_label)
                                            
                                            old_hash = "none"
                                            if image_title in old_image_data:
                                                old_hash = old_image_data[image_title]["Hash"]

                                            file_hash = retrieve_and_save_img(doc_images[img_uri_tag], image_title, club_directory_path, old_hash)
                                            # image is retrieved and saved in the correct folder.
                                            # nothing is saved to the club_data dict because the images get sent via HTTP request regardless.

                                            # add a section in the dict that indicates that an image exists, which is so that the front-end knows to make another request specifically for the image
                                            if file_hash != "none":
                                                club_data["Images"][image_title] = {}
                                                club_data["Images"][image_title]["Hash"] = file_hash

                                    elif table_row["tableCells"][0]["content"][0]["paragraph"]["elements"][0]["textRun"]["content"].replace("\n", "") == "Links":
                                        # if table row is in links section
                                        club_data["Events"][event_label]["Links"] = {}
                                        for paragraph_elements in table_row["tableCells"][1]["content"][0]["paragraph"]["elements"]:
                                            # iterates through the paragraph elements in the table cell until it reaches one with a valid link
                                            if "link" in paragraph_elements["textRun"]["textStyle"]:
                                                club_data["Events"][event_label]["Links"][paragraph_elements["textRun"]["content"]] = paragraph_elements["textRun"]["textStyle"]["link"]["url"]
                            elif "table" in full_doc[index + j + k] and full_doc[index + k + j]["table"]["tableRows"][0]["tableCells"][0]["content"][0]["paragraph"]["elements"][0]["textRun"]["content"].replace("\n", "")[0:10] == "All fields":
                                # if the second table with the dates has been reached
                                for table_row_index, table_row in enumerate(full_doc[index + k + j]["table"]["tableRows"]):
                                    cell_header = table_row["tableCells"][0]["content"][0]["paragraph"]["elements"][0]["textRun"]["content"].replace("\n", "")
                                    deadline_types = ["Signup Deadline", "Start Date/Time (required)", "End Date/Time"]
                                    if cell_header in deadline_types:
                                        month = table_row["tableCells"][1]["content"][0]["paragraph"]["elements"][0]["textRun"]["content"].replace("\n", "").replace(" ", "").lower()
                                        date = table_row["tableCells"][2]["content"][0]["paragraph"]["elements"][0]["textRun"]["content"].replace("\n", "").replace(" ", "").lower()
                                        year = table_row["tableCells"][3]["content"][0]["paragraph"]["elements"][0]["textRun"]["content"].replace("\n", "").replace(" ", "").lower()
                                        time = table_row["tableCells"][4]["content"][0]["paragraph"]["elements"][0]["textRun"]["content"].replace("\n", "").replace(" ", "").lower()

                                        new_formatted_date = format_dates_properly(month, date, year, time)
                                        if new_formatted_date == "error":
                                            if cell_header == "Start Date/Time (required)":
                                                # if the required field is not correctly filled in, delete the entire event from the dict.
                                                del club_data["Events"][event_label]
                                                break
                                        else:
                                            #TODO: make it so that the start time can't be later than the end time.
                                            club_data["Events"][event_label][cell_header.replace(" ", "_").replace("/", "_")] = new_formatted_date

    #dump_to_json(club_file_path, club_data["Metadata"]["Club_Name"].replace(" ", "_").lower(), club_data)
    dump_data_file(club_data, club_directory_path + "/" + club_data["Metadata"]["URL"].replace(" ", "_").lower() + ".json")

    club_listing = {}
    club_listing = club_data["Metadata"]
    club_listing["Images"] = club_data["Images"]

    return club_listing