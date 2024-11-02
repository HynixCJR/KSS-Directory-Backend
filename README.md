# KSS Directory Backend
This is the repo for KSS Directory's backend, which includes the following functions of the service:
- Discord Bot
- Web Server
- Club Repository Retriever
- Google Forms Retriever

Note that this is only the backend of KSS Directory; the frontend repository can be found [here](https://github.com/kssdirectory/KSS-Directory-Website).
This README.md file serves as documentation for the KSS Directory Backend.

## Table of Contents
Use this section to navigate through the documentation.
The documentation is currently unfinished.

1. [General Maintainer Documentation](#general-maintainer-documentation)
3. [Installation and Project Structure](#installation-and-project-structure)
4. [Discord Bot](#discord-bot)
5. [Web Server](#web-server)
6. [Club Repository Retriever](#club-repository-retriever)
7. [Google Cloud Backend](#google-cloud-hosting)
8. [Vercel Frontend](#vercel-frontend)
9. [Custom Image Caching](#custom-image-caching)

# General Maintainer Documentation
This section will be updated later. For now, see [the Google Docs version](https://docs.google.com/document/d/1ngnna95KSxb0117wMao7gFBE8yUne6eFYDhBZlVmU-s/edit)
1. [Assigning club role names](#assigning-club-role-names)
    - [How to assign club role names](#How-to-assign-club-role-names)
    - [Checking current club role names](#Checking-current-club-role-names)
3. [Adding club details](#adding-club-details)
    - [Adding club social media links](#adding=club-social-media-links)
5. [Adding Announcements](#Adding-announcements)

## Assigning Club Role Names
### How to assign club role names
Before you add an announcement, it is highly recommended that you assign a specific name to each club/event first, assuming one has not already been added. These names are what show up on the [website](https://kss.directory) instead of the role on Discord.

Assigning a name to the club/event before you send an announcement is very important, as an announcement cannot be edited after it has been sent already. In other words, the announcement in the second image above would remain that way (unless it were deleted), even if the role was assigned after the fact. Because of this importance, it is recommended that role names are assigned as soon as a new role is added to the Discord server.



# Installation and Project Structure
The overall structure of the KSS Directory project can be found in [this Figma project](https://www.figma.com/design/FAIIxUnNkmq4BIWFSOw9CA/Project-Structure?node-id=1-2&t=wHYSEHABe5N3px59-1).

Required:
- [Python](https://www.python.org/downloads/) is used for the back end. After installing Python, run the following in the Python terminal:
  - ```pip install discord``` to install Discord.py library.
  - ```pip install dotenv``` to install dotenv library.
  - ```pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib``` to install Google Client library.
  - ```pip install fastapi``` to install FastAPI
  - ```pip install pytz``` to install pytz
  - ```pip install 'uvicorn[standard]'``` to install Uvicorn.
- [NodeJS](https://nodejs.org/en/download/prebuilt-installer/current) is used for the front end.
  - After installing NodeJS, run ```npm install next@latest react@latest react-dom@latest``` in the terminal to install NextJS, which is the JS/React framework that the front end uses.
  - Run ```npm install --save react-modal``` to install react-modal, which is used to create popups on the KSS Directory website.

# Web Server
We run an NGINX reverse proxy with Certbot to HTTPS encrypt the backend, which forwards requests directly to a webserver written in python using FastAPI. 

# Google Cloud Hosting
All our backend infrastructure (All the systems in this repository) is hosted on a Google Cloud VM. We use the standard networking tier, and a static IP for our VM. Both of these resources are included in Google Cloud's free tier. For accessing the API, we use a subdomain of the kss.directory hostname to point to our api. You see our live API at [https://api.kss.directory](https://api.kss.directory). Using a subdomain of the main website's domain also allows us to conveniently avoid issues with browser CORS policies. 

# Vercel Frontend
The frontend for KSS Directory is hosted on Vercel, more information can be found on the frontend repository located [here](https://github.com/kssdirectory/KSS-Directory-Website)

# Custom Image Caching
Vercel (The platform hosting KSS Directory's frontend) in combination with NextJS automatically caches images on it's edge network for faster page loads, but places limits on how many images can be optimised over a billing cycle. Since the images on the backend change with some regularity, it's important to refresh vercel's cached image quickly. Unfortunately NextJS has no built in way to invalidate specific portions of it's image cache, the only option to refresh images is to change the URL used to equest them. To avoid using unnessesary resources we could potentially be billed for, since each unique URL is considered another image for vercel to optimise, the frontend first request the hash of the image from the webserver, which is then appended to the image request URL, ensuring the URL only changes when the underlying image does. 

We also optimise for bandwidth by converting any image on the backend to webP, which reduces the amount of bandwidth out from the backend server, which is limited at 200GB by Google Cloud's free tier.