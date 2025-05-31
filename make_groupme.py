#------------------------------------------------------------------------
#
#   (`\ .-') /`   ('-. .-. .-')          _ .-') _     ('-.        (`-.   
#    `.( OO ),' _(  OO)\  ( OO )        ( (  OO) )  _(  OO)     _(OO  )_ 
# ,--./  .--.  (,------.;-----.\         \     .'_ (,------.,--(_/   ,. \
# |      |  |   |  .---'| .-.  |   .-')  ,`'--..._) |  .---'\   \   /(__/
# |  |   |  |,  |  |    | '-' /_)_(  OO) |  |  \  ' |  |     \   \ /   / 
# |  |.'.|  |_)(|  '--. | .-. `.(,------.|  |   ' |(|  '--.   \   '   /, 
# |         |   |  .--' | |  \  |'------'|  |   / : |  .--'    \     /__)
# |   ,'.   |   |  `---.| '--'  /        |  '--'  / |  `---.    \   /    
# '--'   '--'   `------'`------'         `-------'  `------'     `-'     
#
#------------------------------------------------------------------------
# Designer   : The Ghost of Joe, Jia
# Version    : 5.21.2025
# Description: Script to help add volunteers to a groupme.
#------------------------------------------------------------------------
"""* VERSION NOTES
 * 1. I am getting a lot of my reference code from here:
    https://github.com/yangzihe/GroupMe-Multi-add/blob/master/README.md
    They are using and older version of python, so I had to update some
    of the API calls, and library calls with the proper name.
 * 2. You will need to create a GroupMe developers account here:
    https://dev.groupme.com/session/new
    see instructions on how to do so.
 * 3. This script runs on python version: Python 3.13.3
 * 4. You will need the reuqests API from the following address:
    https://github.com/psf/requests
    tbh, you don't really need it if you got all the code and stuff from me.
    It will stay at this version until they update anything.
 * 5. Used the following for reference:
    https://dev.groupme.com/docs/v3
 * 6. For reference on installing the latest maintained version of requests,
    you can look here (but the instructions here are a little out of date):
    https://docs.python-requests.org/en/latest/user/install/#install
    It was really that you need to cd in "requests-main" and run python -m pip install .
 
*"""
#------------------------------------------------------------------------
import requests
import csv
import os
import time
import random
from datetime import datetime

#CONFIGURATION - Locally, each user will have to create a GroupMe
#Developer account, and copy and paste their access token here.
ACCESS_TOKEN = ""

#Constructing the path to the downloads folder. It is possible that the path
#is different, but this should be the default one.
download_path = os.path.join(os.path.expanduser('~'), 'Downloads')

#This is a tough one, because GroupMe no longer makes it clear what
#Group ID is.I was able to find it with the following API call:
#curl -X GET "https://api.groupme.com/v3/groups?token=<YOUR_ACCESS_TOKEN>"
#The problem is that this is going to return EVERY chat you are in.
#Also this only works in Command Prompts (not terminals, and idk what the apple
#equivalent is.)
#Which makes it a bit difficult to figure out what it is.
#Alternativly, you can also go to the GroupMe chat, copy the link
#To invite someone, and you should be able to get the group id there
#It should look something like this:
#https://groupme.com/join_group/1234567890/7xeszbox
#Where the group id is 1234567890.
#See instructions on how to fill it out after.
GROUP_ID = input("Enter Group ID:")

#Users should download volunteer information from the Jotform Google Sheet and name it
#something like "volunteersNumbers.csv" 

#So the purpose of this function is to check the user's download folder for the most recent
#download of the "volunteersNumbers(n).csv" where 'n' denotes an arbitrary 'file with a same
#name' number. The motivation behind this function is so that the user doesn't necessarily
#need to maintain their downloads folder and can keep multiple iterations of
#"volunteersNumbers.csv" if they forget to rename or delete old files. Another motivation is
#to reduce the amount of file navigation on the user's end to give the user a friendlier
#program to run. -Jia (Which coincidentally happens to be Joe but the vowels are 'shifted up'
#by one position.

#Here, we define "newest_volunteer_information" to grab the most recent file containing
#volunteer information. It takes the path to the directory we want to search as an input and
#returns the path to a specific file. Or, in this case, it takes the path to the "Downloads"
#directory as an input and should spit out the latest "volunteersNumbers(n).csv" where 'n'
#denotes an arbitrary 'file with a same name' number.

paths = []
def newest_volunteer_information(path):

    #os.listdir() basically just gives us the names of everything in the directory in a list.
    #We can probably filter this list for only relevant files, but I'm not that smart XD.

    files = os.listdir(path)

    #Here, I decided to sort our list for only files containing a specific keyword. Since
    #folks will (hopefully) be remembering to rename the google sheet to "voluntersNumbers",
    #the .csv file they'll be downloading will also contain that in the name, followed by a
    #number if the user hasn't deleted their old files yet. I used the keyword 'volunteer'
    #but the word can be more specific if desired for accuracy.

    for basename in files:
        if 'volunteer' in basename:

            #Here, we just combine the file names to the directory path to get a path directly
            #to the file.

            paths.append(os.path.join(path, basename))
            
    #Check to see if we have any files properly named. If no files are properly named, send
    #an error message.
    if not paths:
        raise TypeError("No files with the proper name!")

    #Now that we have a list of all the relevant files in the Downloads folder, we can check
    #which is the most recent. And to make sure the file isn't outdated, for instance, if the
    #user forgot to download the file for the current week's drop, we can compare the file's
    #path creation time (for Windows machines, may be dependent on system) to the current
    #system time. I'm using a window of 2 hours (converted to seconds) but feel free to change
    #to more useful time frames.

    recent_file = max(paths, key=os.path.getctime)
    file_time = os.path.getctime(recent_file)
    if (time.time() - file_time) <= 7200:
        if recent_file.endswith('.csv'):
            return recent_file
        else:
            raise TypeError("Make sure to download the Google Sheet as a .csv file!")
    else:
        raise TypeError(rf"Please go download the latest file and ensure it's named properly!")

CSV_FILE = newest_volunteer_information(download_path)


#Function to Read CSV
#Pretty straight forward - we have a memers array that will go 
#and add all the members iteratively. This array is then used below
#in the API calls to automate the adding of people. It is in a try-catch
#in case there are any errors, but the JotForm should have sent the data correctly
#barring any user error. You may need to fix the data if that's the case.
#The csv file should look like this (yes this means include the braces and hyphen):
#John Doe,(323)555-5555
def load_members_from_csv(csv_filename):
    members = []
    try:
        with open(csv_filename, "r", encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if len(row) == 4:  # Ensure correct format (First Name, Last Name, Pronouns, Phone Number)
                    #Formatting Pronouns with Parentheses. There is a better way to do it but this works?
                    if row[2]:
                        if (row[2][0] != '(') & (row[2][0] != '[') & (row[2][0] != '{'):
                            row[2] = '(' + row[2] + ')'
                    #Combining first names, last names, and prononuns into one entry
                    if not row[1]:                   
                        #Handling cases where volunteer omits their last name differently for formatting
                        members.append({"nickname": row[0] + row[2], "phone_number": row[3]})
                    else:                        
                        #Adding a space between first and last name for formatting
                        members.append({"nickname": row[0] + ' ' + row[1] + row[2], "phone_number": row[3]})
    except Exception as e:
        print(f"Error reading CSV: {e}")
    return members

#Function to Add Members to GroupMe
#Pretty self explanitory - All built in API in the libraries we installed.
#Shout-out open source.
def add_members_to_group(group_id, members):
    url = f"https://api.groupme.com/v3/groups/{group_id}/members/add"
    payload = {"members": members}
    headers = {"Content-Type": "application/json", "X-Access-Token": ACCESS_TOKEN}
    
    response = requests.post(url, json=payload, headers=headers)
    
    #I have never seen 201. But when I googled 202, it says that it is code
    #related to a syncing issue, and the members are added, just not immediately
    #the time difference is like a second. I am calling it a success here, but still
    #check if the volunteers got added. 
    if response.status_code == 201:
        dramatic_effect()  # Call the binary stream effect function
        print("Members successfully added!")
    elif response.status_code == 202:
        dramatic_effect()  # Call the binary stream effect function
        print("Members successfully, just give it some time.")
    else:
        print(f"Error adding members: {response.status_code} - {response.text}")

"""
The following function does absolutly nothing! It is just a troll! 🤣
Also, I found out that Windows supports emojis (which is the type of os this
code was developed on). 
Based on the minute at which this code is run, it will either do one of two things:
1. Print a stream of binary code to make the script look like it is doing more than what
it is actually doing (it looks like you are entering the matrix lmao)
2. A little jump scare to new users which will say that everyone's data is uploaded to
the dark web (it's not lol)
The troll displayed on the console depends on whether the minute is odd or even.
If you are teaching this script to someone, have fun trolling! 🤣
"""
def dramatic_effect():
    current_minute = datetime.now().minute

    #I just did a modulo 2, if it's even, the remainder is 0, therefore, print binary stream
    if current_minute % 2 == 0:  # EVEN minute -> Binary stream effect
        print("Initiating script (there is no turning back now!)...\n")
        for _ in range(500):  # Prints 30 lines of binary code
            line = "".join(str(random.randint(0, 1)) for _ in range(100))  # 100 random 0s and 1s
            print(line)
            time.sleep(0.05)  # Slight delay for effect
        print("\nThe process is complete...we are safe!")

    #if the if statement doesn't execute, jump scare!
    else:  # ODD minute -> Fake "Dark Web" panic 🤣
        print("Uh-oh... everyone's data is now on the dark web! 😨")
        time.sleep(5)  # Wait 5 seconds for suspense
        print("Nah jk, the GroupMe was created successfully 😆🎉")

#Main Execution
members = load_members_from_csv(CSV_FILE)
#DEBUGGING LINE
#print(members)
if members:
    add_members_to_group(GROUP_ID, members)
else:
    print("No members loaded from CSV.")
