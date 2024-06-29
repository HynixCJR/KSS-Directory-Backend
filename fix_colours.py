import json, random

# put this file in the same directory as pings.json
# colour data stored 


pingsFile = open("pings.json", "r+")
pings = json.loads(pingsFile.read())


clubCatFile = open("clubCategoryInfo.json", "r+")
clubCatInfo = json.loads(clubCatFile.read())

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

# removes all stuff in json from 0th position
pingsFile.truncate(0)

# moves cursor back to 0th position
pingsFile.seek(0)

# json.dumps changes pings to str
pingsFile.write(json.dumps(pings))
pingsFile.flush()



# removes all stuff in json from 0th position
clubCatFile.truncate(0)

# moves cursor back to 0th position
clubCatFile.seek(0)

# json.dumps changes pings to str
clubCatFile.write(json.dumps(clubCatInfo))
clubCatFile.flush()


# # debugging purposes
# temp_list = []
# for key, value in pings.items():
#     if value[2] not in temp_list:
#         temp_list.append(value[2])
# print(temp_list)
