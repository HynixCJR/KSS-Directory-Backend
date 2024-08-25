import json, random
from FileHelper import *

# put this file in the same directory as pings.json
# colour data stored 


pings = load_data_file("data/pings.json")

clubCatInfo = load_data_file("data/clubCategoryInfo.json")

# sets clubCatColours to a list with all the category 
# colours available, so that there are no duplicate
# colours when a new one gets randomly chosen.
clubCatColours = []
for key, value in clubCatInfo.items():
    clubCatColours.append(value)

for key, value in pings.items():
    if value[1] in clubCatInfo:
        pings[key][2] = clubCatInfo[value[1]]
    else:
        while True:
            randomNum = random.randint(0,360)
            if randomNum not in clubCatColours:
                clubCatColours.append(randomNum)
                pings[key][2] = randomNum            
                clubCatInfo[value[1]] = randomNum
                break
            else:
                break

dump_data_file(pings, "data/pings.json")

dump_data_file(clubCatInfo, "data/clubCategoryInfo.json")

# # debugging purposes
# temp_list = []
# for key, value in pings.items():
#     if value[2] not in temp_list:
#         temp_list.append(value[2])
# print(temp_list)
