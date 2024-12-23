# This is the main Discord bot file!
# If you want to run the Discord bot, run this file.

# you need discord.py installed to run this
# You can run the following command in command prompt or terminal (if you're on Windows) to install, excluding the '#'
# py -3 -m pip install -U discord.py
import discord

from pathlib import Path

import json
import glob
from dotenv import dotenv_values
from datetime import datetime
import random as r

import os

from FileHelper import *
import pytz

# Enable debug mode (Uses seperate bot in testing server)
debug_mode = False

# Opening the pings.json file
pings = load_data_file("data/pings.json")

# Opening the clubInfo.json file
clubInfo = load_data_file("data/clubInfo.json")

# Stuff that initializes the Discord bot
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


# Load existing variables from the .env.shared file
env_vars_shared = dotenv_values('.env.shared.debug' if debug_mode else '.env.shared')

# global variables
formattedDate = ""
"""The final date in ISO 8601 format for better file organization"""
previousDate = ""

anceNum = 1
"""The number of announcements sent so far, excluding the date identifier."""

def iterateSect(msg, mod, iter, iterEnd, endSymb):
    """Iterates through a specified message until it reaches a specific character, returning the full word up to the specified character and the final iterate value."""

    while True:
        if msg[iter] != endSymb:
            mod += msg[iter]
            iter += 1
        else:
            iter += iterEnd
            break

    return mod, iter

def saveClubInfo(clubPing, clubInfoType, clubInfoTypeLabel, message):
    global clubInfo, pings

    clubName = pings[clubPing][0]
    if clubName not in clubInfo:
        clubInfo[clubName] = {}
    clubInfo[clubName].update({clubInfoTypeLabel: message[len(clubPing) + len(clubInfoType) + 3:]})

    dump_data_file(clubInfo, "data/clubInfo.json")
    print("=====================\nClubInfo updated to\n " + str(clubInfo) + "\n=====================")
    

async def difChannel(channel, msgTitle, msgDescription, embedColour):
    """Sends an embed message to the specified channel. This function must be called with an "await" in front of it."""
    print("-> Sent message in channel ID: " + str(channel) + " with content:\n " + str((msgTitle, msgDescription)) + "\n=====================")
    embed = discord.Embed(colour = embedColour, title = msgTitle, description = msgDescription)
    sendChannel = client.get_channel(channel)
    #await client.wait_until_ready()
    await sendChannel.send(embed = embed)



@client.event
async def on_ready():
    """This function activates when the bot first starts up."""
    print(f'We have logged in as {client.user}')


def load_latest_date():
    global formattedDate, previousDate

    if formattedDate == "":
        print("Bot started with no date. Loading latest datefile")
        all_ance = sorted(glob.glob("announcements/*.json"))
        lastWrittenDatefileName = Path(all_ance[-1]).stem

        # sanity check
        if os.path.isfile("announcements/" + lastWrittenDatefileName + ".json"):
            previousDate = lastWrittenDatefileName
            formattedDate = lastWrittenDatefileName
            print("Loaded date: " + lastWrittenDatefileName)
        else:
            print("Failed to load latest datefile. Either this is a bug or the directory is empty.")

@client.event
async def on_message(message):
    """This function activates if a new message is sent."""

    print("New message in channel with ID " + str(message.channel.id))

    global formattedDate, anceNum, previousDate

    if message.author == client.user:
        return

    if message.channel.id == int(env_vars_shared['anceChnl']):
        previousDate = formattedDate
        load_latest_date()
        # Checks if a message was sent the announcements channel

        
        if message.content.startswith('**'):
            # Trigger for start of new announcement, which starts with a ** to signify the day of the week being bold.
            oldAnceNum = anceNum
            anceNum = 1
            iterate = 2
            
            # Getting the day of the week
            day = ""
            day, iterate = iterateSect(message.content, day, iterate, 6, "*")

            # Getting the month
            month = ""
            try:
                month, iterate = iterateSect(message.content, month, iterate, 1, " ")
            except:
                print("Error iterating month")
            month = json.loads(env_vars_shared['months']).get(month.lower())
            if month == None:
                await difChannel(int(env_vars_shared['debugChnl']), "**Error!**", "There was an error with the message you sent!\n```" 
                                 + message.content 
                                 + "```\nThe month specified was not recognized, is it spelled and formatted correctly?\n\nThe expected format was as follows:\n```"
                                 + "**[DAY]**\n\n**[MONTH] [DATE], [YEAR]**```\nMore details are accessible with the .help command.",  
                                 int(env_vars_shared['negColour']))
                await message.delete()
                return # give up early if can't parse date

            # Getting the date
            date = ""

            # Note that I don't use the iterateSect function here because the if statement is different
            while True:
                if ord(str(message.content[iterate])) in range(48,58):
                    date += str(message.content[iterate])
                    iterate += 1
                else:
                    while True:
                        if ord(message.content[iterate]) in range(97,123) or message.content[iterate] == "," or message.content[iterate] == " ":
                            iterate += 1
                        else:
                            break
                    break

            # For the sake of organization, I am making it so that all dates are a length of 2
            if len(date) == 1:
                date = "0" + date

            # Getting the year
            # It's easier to not use the iterateSect function here
            year = ""
            for i in range(iterate, len(message.content) - 1):
                if message.content[i] == "*":
                    break
                else:
                    year += message.content[i]

            # iterate should point to somewhere on final line of a valid date entry
            # just check if there are more
            for i in range(iterate, len(message.content) - 2):
                if message.content[i] == "\n":
                    await difChannel(int(env_vars_shared['debugChnl']), "**Error!**", "There was an error with the message you sent!\n```" + message.content + "```\nThere was additional content after the date identifier, and so the message you sent has been deleted.", int(env_vars_shared['negColour']))

                    # Deleting the message and resetting the formattedDate to the previousDate.
                    await message.delete()

                    # restore old state
                    anceNum = oldAnceNum
                    return # give up
            
            # Making the date info into a dictionary
            dateInfo = {
                0: [day, year, month, date]
            }
            
            # Formatting the year, month and date into ISO format, which is better for file organization
            formattedDate = year + month + date

            # oh god why is it like this
            # the VALID case is when we ERROR
            # it doesn't check the file's existance, it just tries to create it and errors when it can't
            # it's SUCCESSFUL when it errors
            # whyyyyyyyyyy
            try:
                # Checking if the announcement file for the specified date exists
                anceData = open("announcements//" + formattedDate + ".json", "r+")
                ance = anceData.read()

                # If there is no error, this sends an error message to the debug channel.
                await difChannel(int(env_vars_shared['debugChnl']), "**Error!**", "There was an error with the message you sent!\n```" + message.content + "```\nThis date already exists in the database, and so the message you sent has been deleted.", int(env_vars_shared['negColour']))
                # Deleting the message and resetting the formattedDate to the previousDate.
                await message.delete()
                formattedDate = previousDate

            except: #### THIS IS SUPPOSED TO BE FOR ERROR HANDLING DAMMIT #### [Inconceivable Rage] ####
                # If there are no issues, then proceed.

                # This is just for debugging, which I am keeping because it is useful to see in the console
                print("New JSON file created at announcements/" + formattedDate + ".json")

                # Sending a success message to the Debug Channel, along with the processed data for debugging purposes.
                await difChannel(int(env_vars_shared['debugChnl']), "**New *Date Identifier* announcement creation successful!**", "The most recent *Date Identifier* announcement was processed successfully. ```" + message.content + "```\nAny club/event announcements you send will henceforth be attached to this Date Identifier (as long as it is formatted it properly), and will be updated as such on the website.\n\nFor debugging purposes, here is what the processed data looks like:\n```" + "Day: " + day + "\n\nYear: " + year + "\nMonth: " + month + "\nDate: " + date + "\n\nJson file name: " + formattedDate + ".JSON```", int(env_vars_shared['posColour'], 16))

                # Creating a new .json file with the formatted date as its name
                with open("announcements/" + formattedDate + ".json", "w") as json_file:
                    # Writing the date information (the dictionary) to the newly created file
                    json.dump(dateInfo, json_file)

        elif message.content.startswith('<@&'):
            # Mentions are read by the bot as <@&...>, and so this checks if the message starts with a ping.

            if formattedDate != "":
                iterate = 0

                # Getting the role that was pinged
                role_id = ""
                role_id, iterate = iterateSect(message.content, role_id, iterate, 3, " ")
                
                try:
                    # setting the role name and category of the announcement
                    role_name = pings[role_id][0]
                    role_cat = pings[role_id][1]
                except:
                    # warning message
                    await difChannel(int(env_vars_shared['debugChnl']), "**Role does not have assigned category!**", '**The role you mentioned, ' + role_id + ', does not have an assigned tag. It has been assigned a "miscellaneous" tag for the time being. You can change it in ' + str(env_vars_shared['rolesChnl']), int(env_vars_shared['midColour']))
                    role_id = role_id.replace("<@&", "")
                    role_id = role_id.replace(">", "")

                    try:
                        role_name = discord.utils.get(message.guild.roles, id = int(role_id)).name
                    except:
                        await difChannel(int(env_vars_shared['debugChnl']), "**There was an errror with the message you sent!**", '```The role you mentioned, ' + role_id + ', is not valid. Check your formatting (there might be a missing space after the role)```', int(env_vars_shared['negColour']))
                        await message.delete()

                        return
                    role_cat = "Miscellaneous"

                # handle extra whitespace
                while message.content[iterate] == "*" or message.content[iterate] == " ":
                    iterate += 1
                
                anceBrief = ""
                while True:
                    if iterate > len(message.content) - 1:
                        await difChannel(int(env_vars_shared['debugChnl']), "**Error!", "There was an error with the message you sent!\n```" + message.content + "```\nUnable to read announcement title, did you format something incorrectly?", int(env_vars_shared['negColour']))
                        await message.delete()

                        return
                    if message.content[iterate] != "*":
                        anceBrief += message.content[iterate]
                        iterate += 1
                    else:
                        try:
                            iterate = message.content.index("\n", iterate) + 1
                        except:
                            iterate = len(message.content)
                            # await difChannel(int(env_vars_shared['debugChnl']), "**Error!", "There was an error with the message you sent!\n```" + message.content + "```\nUnable to read announcement description, did you format something incorrectly?", int(env_vars_shared['negColour']))
                            # await message.delete()

                            # return
                        break
                
                print(message.content)
                anceBrief = anceBrief.strip()
                
                anceDtls = ""
                for i in range(iterate, len(message.content)):
                    anceDtls += message.content[i]
                anceDtls = anceDtls.strip(">") # Strip special characters
                anceDtls = anceDtls.replace("*", "")
                anceDtls = anceDtls.strip() # strip trailing whitespace

                # Error if last date identifier does not match today's date
                todayDateID = datetime.now(pytz.timezone('EST')).strftime('%Y%m%d')
                if formattedDate != todayDateID:
                    sendChannel = client.get_channel(int(env_vars_shared['debugChnl']))
                    await sendChannel.send("<@" + str(message.author.id) + "> **Warning!**")
                    await difChannel(int(env_vars_shared['debugChnl']), "**The latest date identifier ``" + str(formattedDate) + "`` does not match today's date identifier of ``" + str(todayDateID) + "``**", "Message content is as follows:\n```" + str(message.content) + "```\nThe announcement still went through, but this may be a mistake, check that you've posted a valid and correct date identifier. If you forgot the date identifier, delete the latest message on discord, as well as with ``.ance purge latest`` to clear it from the database, and start over.", int(env_vars_shared['negColour']))

                anceFile = open("announcements/" + formattedDate + ".json", "r+")
                ance = json.loads(anceFile.read())
                
                ance.update({str(anceNum): [role_cat, role_name, anceBrief, anceDtls]})

                anceNum += 1

                # removes all stuff in json from 0th position
                anceFile.truncate(0)

                # moves cursor back to 0th position
                anceFile.seek(0)

                # json.dumps changes pings to str
                anceFile.write(json.dumps(ance))
                anceFile.flush()
   
                
                # Sends confirmation message to debug channel
                await difChannel(int(env_vars_shared['debugChnl']), "**New *Club/event/info* announcement creation successful!**", "The most recent *Club/event/info* announcement was processed successfully. ```" + message.content + "```\nFor debugging purposes, here is what the processed data looks like:\n```" + "Club/event/info name: " + role_name + "\nClub/event/info category: " + role_cat + "\n\nBrief announcement: " + anceBrief + "\nAnnouncement details: " + anceDtls + "```", int(env_vars_shared['posColour'], 16))
                
                print("=====================\nSaved ance with data:\n" + str(ance[str(anceNum - 1)]) + "\nTo file " + formattedDate + ".json")

            else:
                # If there is no prior Date Identifier announcement to refer to

                # Sends error message to debug channel
                await difChannel(int(env_vars_shared['debugChnl']), "**Error!", "There was an error with the message you sent!\n```" + message.content + "```\nThere is no date associated with your announcement. Please send a properly formatted date first, then send an announcement. Thanks!", int(env_vars_shared['negColour']))
                await message.delete()

    elif message.channel.id == int(env_vars_shared['rolesChnl']):
        # Check if message is in the roles channel

        if message.content.startswith('<@&'):
            # adding or updating the roles
            # also adding extra club/event info, such as meeting dates and descriptions

            newRoleID = ""
            newRoleName = ""
            newRoleSect = ""

            if message.content[message.content.find(">") + 2] == ".":
                for i in json.loads(env_vars_shared['clubInfoTypes']):
                    if message.content[message.content.find(">") + 2:].startswith(i[0]):
                        if str(message.content[0:message.content.find(">") + 1]) in pings:
                            saveClubInfo(str(message.content[0:message.content.find(">") + 1]), i[0][1:], i[1], message.content)
                            await message.channel.send("Role data updated.")
                        else:
                            await difChannel(int(env_vars_shared['debugChnl']), "**Error!", "There was an error with the message you sent!\n```" + message.content + "```\nYou have not added the ping to a club/event yet, so info about the club/event cannot be added.", int(env_vars_shared['negColour']))
            
            elif len(message.content) < 100 and "," in message.content and "<@&" in message.content:
                # Basic error checking (seeing if length is too long, and if there is a comma)

                iterate = 0
                while True:
                    if message.content[iterate] != " ":
                        newRoleID += message.content[iterate]
                        iterate += 1
                    else:
                        iterate += 1
                        break
                while True:
                    if message.content[iterate] != ",":
                        newRoleName += message.content[iterate]
                        iterate += 1
                    else:
                        iterate += 2
                        break
                for i in range(iterate, len(message.content)):
                    newRoleSect += message.content[i]
                
                clubCatFile = open("data/clubCategoryInfo.json", "r+")
                clubCatInfo = json.loads(clubCatFile.read())

                # Sets clubCatColours to a list with all the category 
                # colours available, so that there are no duplicate
                # colours when a new one gets randomly chosen.
                # Also sets clubCatNames to list with all category names,
                # which makes it easier to find if there's a new category.
                clubCatNames = []
                clubCatColours = []
                for key, value in clubCatInfo.items():
                    clubCatNames.append(key)
                    clubCatColours.append(value)
                
                if newRoleSect in clubCatNames:
                    # If the new role's category already exists, set it to the determined colour code.
                    randomColour = clubCatInfo[newRoleSect]

                else:
                    # If the new role's category doesn't exist already, set it to a random colour code
                    # that is NOT already taken by an existing role category.

                    while True:
                        randomColour = r.randint(0,360)
                        if randomColour not in clubCatColours:
                            clubCatColours.append(randomColour)

                            clubCatInfo[newRoleSect] = randomColour
                            # removes all stuff in json from 0th position
                            clubCatFile.truncate(0)
                            # moves cursor back to 0th position
                            clubCatFile.seek(0)
                            # json.dumps changes pings to str
                            clubCatFile.write(json.dumps(clubCatInfo))
                            clubCatFile.flush()
                            break


                pings.update({newRoleID: [newRoleName, newRoleSect, randomColour]})

                dump_data_file(pings, "data/pings.json")
                # # removes all stuff in json from 0th position
                # pingsFile.truncate(0)

                # # moves cursor back to 0th position
                # pingsFile.seek(0)

                # # json.dumps changes pings to str
                # pingsFile.write(json.dumps(pings))
                # pingsFile.flush()
                await message.channel.send("Role ``" + newRoleName + "`` updated.")
                print("=====================\nSaved ping with data:\n" + str(pings[newRoleID]) + "\nTo pings.json")

            # error messages
            elif len(message.content) > 100:
                await message.channel.send("Sry, I think there was an error. Ur message is too long!")
            elif "," not in message.content:
                await message.channel.send("Sry, I think there was an error. Ur message does not have a comma!")
            elif "<@&" not in message.content:
                await message.channel.send("Sry, I think there was an error. You didn't add a ping!")
        
        elif message.content.startswith('.roles'):
            # Debugging cmd for the admins of the KSS Directory server
            if len(message.content) > 25:
                await message.channel.send("Okay, here is the info for the role you requested.")
                try:
                    print(pings[message.content[7:]])
                    await message.channel.send(message.content[7:] + ": **Name:** " + pings[message.content[7:]][0] + ", **Category:** " + pings[message.content[7:]][1])
                except:
                    await message.channel.send("Sorry, the role " + message.content[7:] + " doesn't seem to have been added yet!")
            elif len(message.content) < 10:
                await message.channel.send("Okay, here are the roles!")
                for [key, value] in pings.items():
                    await message.channel.send(str(key) + ": **Name**: " + value[0] + ", **Category**: " + value[1])
            else:
                await message.channel.send("There was an error with the message you sent.")

        elif message.content.startswith('.roleremove'):
            # removes a role from the pings json file.
            
            if " " in message.content[12:]:
                roleRemove = message.content[12:].replace(" ", "")
            else:
                roleRemove = message.content[12:]
            
            await message.channel.send("Okay, removing the role " + roleRemove + " from the database!")

            try:
                pings.pop(roleRemove)
                dump_data_file(pings, "data/pings.json")

                # # removes all stuff in json from 0th position
                # pingsFile.truncate(0)

                # # moves cursor back to 0th position
                # pingsFile.seek(0)

                # # json.dumps changes pings to str
                # pingsFile.write(json.dumps(pings))
                # pingsFile.flush()
                print("=====================\nRemoved ping:\n" + str(roleRemove) + "\n frome pings.json\nFile contents are as follows:\n" + str(pings))
            except:
                await message.channel.send("Sorry, there was an error! This might be because " + roleRemove + " doesn't exist in the database, so there is nothing to remove. :(")
        
        # Clear caf menu from website
        elif message.content.startswith('.clear cafmenu'):
            data = load_data_file("data/gforms_output_data.json")
            data["cafeteria_data"] = []
            dump_data_file(data, "data/gforms_output_data.json")
            await difChannel(int(env_vars_shared['rolesChnl']), "Success!", "Cleared cafeteria menu file!", int(env_vars_shared['posColour']))

        elif message.content.startswith('.club info'):
            # Returns the stored club info.

            if len(message.content) < 11: # List all clubs
                await message.channel.send("Here is a list of the club info currently stored by this bot.")
                for [clubKey, clubData] in clubInfo.items():
                    await message.channel.send("**Name:** " + clubKey)
                    
                    clubDataMessage = ""
                    for [dataType, data] in clubData.items():
                        clubDataMessage += "> **" + dataType + ":** " + str(data) + "\n"
                    await message.channel.send(clubDataMessage)
                
                await message.channel.send("...\n\nBy the way, here are the commands you can send to add or edit club/event info.")
                
                for i in json.loads(env_vars_shared['clubInfoTypes']):
                    await message.channel.send("<@&" + str(env_vars_shared['exampleRole']) + "> " + i[0] + " details")
            elif len(message.content) > 30: # List specific club data
                if " " in message.content[10:]:
                    clubInfoTypesRole = message.content[10:].replace(" ", "")
                else:
                    clubInfoTypesRole = message.content[10:]
                try:
                    if clubInfoTypesRole in pings:
                        clubName = pings[clubInfoTypesRole][0]
                        await message.channel.send("Okay, here are the details specifically for " + clubInfoTypesRole + ", otherwise known as **" + clubName + "**:")

                        if clubName in clubInfo:
                            clubDataMessage = ""
                            for [dataType, data] in clubInfo[clubName].items(): 
                                clubDataMessage += "> **" + dataType + ":** " + str(data) + "\n"
                            await message.channel.send(clubDataMessage)

                            await message.channel.send("...\n\nBy the way, here are the example commands you can send to set or overwrite the club/event details.\n\n...")
                        else:
                            await message.channel.send("...\n\nSorry, I couldn't find any details for the role you specified. You can add some by sending the following commands:\n\n...")
                    else:
                        await message.channel.send("...\n\nSorry, I couldn't find the role you specified. You can see how to create it here:\nhttps://docs.google.com/document/d/1ngnna95KSxb0117wMao7gFBE8yUne6eFYDhBZlVmU-s/edit#bookmark=id.rj0h3b2pnya6\nOnce created, you can add some data to it using the following commands:\n\n...")
                        
                except:
                    await message.channel.send("Sorry, there was an error! Are you sure you typed in the command correctly?")
                
                for i in json.loads(env_vars_shared['clubInfoTypes']):
                    await message.channel.send("<@&" + str(env_vars_shared['exampleRole']) + "> " + i[0] + " details")
            else:
                await message.channel.send("Sorry, there was an error! Are you sure you typed in the command correctly?")

    elif message.channel.id == int(env_vars_shared['debugChnl']):
        if message.content == ".help":
            await message.channel.send("**Hello there! Thank you for using the KSS Directory bot.\nIt is important that you abide by the standard so that the bot and website can actually work. Here is how to send properly formatted announcements:**\n...")
            await message.channel.send("Full announcements are comprised of two parts: a **Date Identifier**, and the actual **club/event** announcements.\nThe date identifier tells users of the Discord server, as well as this bot, what date your announcement is.\n\nIt must follow this format:\n```\n**{day of the week}**\n\n**{month} {date} {year}**\n```\n\nFor example, here is a properly formatted Date Identifier.\n```\n**SUNDAY**\n\n**July 23rd 2023**```\n\nWhich produces the following:\n\n**SUNDAY**\n\n**July 23rd 2023**\n\n*Note that you MUST include the 'rd', 'st', or 'th' after the date.\nMake sure to not include any spaces or characters other than those that are needed!")
            await message.channel.send("...\nClub/event announcements are the actual announcements for KSS clubs and events.\nTo send one of them, you must first initialize the announcements for the day with a Date Identifier. The announcements that follow will then be linked to that date.\n\nThese announcements follow this specific format:\n```\n@{ping} **{announcement brief}**\n*{announcement details}*``` \n Note that this will not work without each of the parts enclosed in {}.\n\nFor example, here is a properly formatted club/event announcement:\n\n```\n@graphic design **Graphic Design Club meeting today at lunch in room 228**\n> *KSDC winners announced, raffle.*\n```\n\nWhich produces the following:\n\n<@&1038542186284859452> **Graphic Design Club meeting today at lunch in room 228**\n> *KSDC winners announced, raffle.*\n\nFor the bot to recognize the message you sent, please make sure that you only have one space after the ping, and one after the >. Also, please make sure you bold/italicize the announcements as shown!")
            await message.channel.send("...\nThe website also assigns new names and categories for each role. You can assign these roles in #temp-roles. Assigning them follows this format:\n\n```\n@{role} {role name}, {role category}\n```\n\nFor example...\n\n```@graphic design Graphic Design Club, Clubs```\n\nproduces the following message:\n\n<@&1038542186284859452> Graphic Design Club, Clubs\n\nThis assigns the name of Graphic Design Club to <@&1038542186284859452>, and puts it in the Clubs category. If you don't do this, the announcements you send will be grouped under the miscellaneous category, and the club/event name will just be the name of the ping.")
        
        elif message.content.startswith('.ance purge latest'):
            load_latest_date()

            if not os.path.isfile("announcements/" + formattedDate + ".json"):
                #print("wtf")
                await difChannel(int(env_vars_shared['debugChnl']), "Uh oh!", "Internal bot error while trying to complete request.\ndateFile for " + formattedDate +".json does not exist.", int(env_vars_shared['negColour']))
                return
            
            data = load_data_file("announcements/" + formattedDate + ".json")
            
            latestAnceNum = 0
            for anceNum, anceData in data.items():
                if int(anceNum) > latestAnceNum:
                    latestAnceNum = int(anceNum)
            
            if latestAnceNum > 0:
                # implicit types are annoying
                latestAnceNum = str(latestAnceNum)

                print("Purging ance # " + latestAnceNum + " from file " + formattedDate + ".json")
                print("Ance content is as follows " + str(data[latestAnceNum]))

                data.pop(latestAnceNum)
                dump_data_file(data, "announcements/" + formattedDate + ".json")


                await difChannel(int(env_vars_shared['debugChnl']), "Success!", "Purged latest announcement from the website database!", int(env_vars_shared['posColour']))
            else:
                print("Purging file " + formattedDate + ".json from database")
                os.remove("announcements/" + formattedDate + ".json")

                formattedDate = ""
                anceNum = 1
                load_latest_date()
                await difChannel(int(env_vars_shared['debugChnl']), "Success!", "Date file was empty, deleting datefile.", int(env_vars_shared['posColour']))


# Client ID of Discord bot

try:
    # Load existing variables from the .env.secret file
    env_vars_secret = dotenv_values('.env.secret')
    clientKey = env_vars_secret['local_token' if debug_mode else 'public_token']
    # if testing locally, switch 'public_token' to 'local_token' in the above.
    # this makes the bot run in the test Discord server, rather than the public KSS Directory server.
except:
    # if the file doesn't exist, prompt user to make one
    print("Error: No .env.secret file found! Please create one and ensure that the 'public_token' or 'local_token' variables are present.")

client.run(clientKey)