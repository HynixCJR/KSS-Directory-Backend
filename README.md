# KSS Directory Backend
This is the repo for KSS Directory's backend, which includes the following functions of the service:
- Discord Bot
- Web Server
- Club Repository Retriever

Note that this is only the backend of KSS Directory; the frontend repository can be found [here](https://github.com/HynixCJR/KSS-Directory-Website).
This README.md file serves as documentation for the KSS Directory Backend.

## Table of Contents
Use this section to navigate through the documentation.

1. [General Maintainer Documentation](#general-maintainer-documentation)
3. [Installation and Project Structure](#installation-and-project-structure)
4. [Discord Bot](#discord-bot)
5. [Web Server](#web-server)
6. [Club Repository Retriever](#club-repository-retriever)
7. [Google Cloud Backend](#google-cloud-hosting)
8. [Vercel Frontend](#vercel-frontend)

# General Maintainer Documentation
This section will be updated later. For now, see [the Google Docs version](https://docs.google.com/document/d/1ngnna95KSxb0117wMao7gFBE8yUne6eFYDhBZlVmU-s/edit)
1. [Assigning club role names](###assigning-club-role-names)
    - [How to assign club role names](####How-to-assign-club-role-names)
    - [Checking current club role names](####Checking-current-club-role-names)
3. [Adding club details](###adding-club-details)
    - [Adding club social media links](####adding=club-social-media-links)
5. [Adding Announcements](###Adding-announcements)

### Assigning Club Role Names
#### How to assign club role names


# Installation and Project Structure
The overall structure of the KSS Directory project can be found in [this Figma project](https://www.figma.com/design/FAIIxUnNkmq4BIWFSOw9CA/Project-Structure?node-id=1-2&t=wHYSEHABe5N3px59-1).

Required:
- [Python](https://www.python.org/downloads/) is used for the back end. After installing Python, run the following in the Python terminal:
  - ```pip install discord``` to install Discord.py library.
  - ```pip install dotenv``` to install dotenv library.
  - ```pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib``` to install Google Client library.
  - ```pip install fastapi``` to install FastAPI
  - ```pip install 'uvicorn[standard]'``` to install Uvicorn.
- [NodeJS](https://nodejs.org/en/download/prebuilt-installer/current) is used for the front end.
  - After installing NodeJS, run ```npm install next@latest react@latest react-dom@latest``` in the terminal to install NextJS, which is the JS/React framework that the front end uses.
  - Run ```npm install --save react-modal``` to install react-modal, which is used to create popups on the KSS Directory website.

