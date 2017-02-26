from urllib2 import urlopen
import os
from shutil import copy2
from datetime import datetime
import sys

repCutoff = 1000
searchURL = "http://forum.kerbalspaceprogram.com/index.php?/search/&type=core_members&sortby=pp_reputation_points&sortdirection=desc&page=[PAGENUMBER]"
Desc_File = "Descriptions.txt"
OutputFile = "RepGrandGroup.txt"
NewMemberTxt = "No Description Yet!"
NameSeparator = "."

members = []


class Member(object):
    def __init__(self):
        self.username = ""
        self.TotalRep = 0
        self.Description = ""
        self.ignore = False
        self.color = ""
        self.profileURL = ""
        
    def __init__(self, name, rep, url, desc):
        self.username = name
        self.TotalRep = int(rep)
        self.profileURL = url
        self.Description = desc
        self.ignore = False
        self.color = ""
        
    def SetDescription(self, desc):
        if desc.startswith("Ignore"): self.ignore = True
        self.Description = desc
        
    def SetColor(self, colorStr):
        self.color = colorStr;


#Pulls a page of the search results from the web, returns the raw page data
def GrabPage(pageNum):
    replacedURL = searchURL.replace("[PAGENUMBER]", str(pageNum))
    print("Grabbing page data from "+replacedURL)
    response = urlopen(replacedURL)
    fullPage = response.read()
    return fullPage
    
#Processes a prefetched search result into a member list for that page, returns the member list and whether the rep threshold was reached
def ProcessPage(pageData):
    done = False
    newMems = []
    index = 0
    while (index >= 0):
        try:
            memberBlockStart = "<li class=\"ipsGrid_span4 ipsStreamItem ipsStreamItem_contentBlock ipsAreaBackground_reset ipsPad ipsType_center\">";
            usernameBlockStart = "data-searchable";
            repBlockStart = "<i class='fa fa-plus-circle'></i>";
            
            
            index = pageData.index(memberBlockStart, index+1)
            
            index = pageData.index(usernameBlockStart, index+1)
            index = pageData.rindex("<a href=", 0, index)
            index += 9
            endURLPos = pageData.index("' data-searchable", index)
            urlString = pageData[index:endURLPos]
            
            #print("urlString: "+urlString)
            
            index = pageData.index(usernameBlockStart, index + 1)
            index = pageData.index("<a href=", index + 1)
            endNamePos = pageData.index("</a>", index)
            substr = pageData[index: endNamePos]
            username = substr.split('>')[1].strip()
            
            #print("username: "+username)
            
            index = pageData.index(repBlockStart, index+1)+len(repBlockStart);
            endRepPos = pageData.index("</span>", index);
            repString = pageData[index: endRepPos].strip();
            
            #print("repStr: "+repString)
            
            rep = int(repString)
            if (rep >= repCutoff):
                newMems.append(Member(username, rep, urlString, NewMemberTxt))
            else:
                done = True
                index = -1
            
        except:
            #print("Error while parsing page. Probably reached the end.")
            index = -1;
        
    #search through the page data and create new members
    return (newMems, done)
    
#Load the descriptions from the file and assign them to the members
def ProcessDescriptions():
    #open the file and read it line by line
    prevUser = "NONE"
    lineNum = 0
    with open(Desc_File, "r") as descFile:
        for line in descFile:
            lineNum += 1
            if line.strip() == "": continue
            try:
                user = line.split('\t')[0].strip()
                desc = line.split('\t', 1)[1].strip();
                member = next((x for x in members if x.username == user), None) #get the member object for a user
                if member != None: #if this member is actually in the list
                    if desc.startswith("[COLOR="):
                        member.SetColor(desc[8:8+7]) #TODO: don't fix this size
                        desc = desc[17:].strip()
                    member.SetDescription(desc)
                prevUser = user
            except:
                print("Caught an exception while parsing the Descriptions file at line {0}. Last successfully parsed member: {1}.".format(lineNum, prevUser))
                print("Error was on this line '{0}'".format(line))
                pass
    return

def SaveRawList():
    with open("raw_list.txt", "w") as f:
        for member in members:
            f.write(member.username+"\n")    

def SaveFinalList():
    with open(OutputFile, "w") as f:
        f.write("[list=1]\n")
        for member in members:
            if not member.ignore:
                f.write("[*]")
                if member.color != "": f.write("[COLOR={0}]".format(member.color))
                f.write("[URL={0}]{1}[/URL]".format(member.profileURL, member.username))
                if member.color != "": f.write("[/COLOR]")
                f.write("{0} {1}\n".format(NameSeparator, member.Description))
        f.write("[/list]")

def FindNewMembers(memberList):
    #curMembers = list(memberList)
    curMembers = []
    for member in memberList:
        curMembers.append(member.username)
    #read through the latest raw_list and remove anyone in it
    if os.path.exists("raw_list.txt"):
        with open("raw_list.txt", "r") as raw:
            for user in raw:
                user = user.strip()
                if user in curMembers:
                    curMembers.remove(user)
    with open("new_list.txt", "w") as new:
        for user in curMembers:
            new.write(user+"\n")
    return len(curMembers)

def BackUpRawList():
    #copy the raw_list.txt file to a new file with yyyy-mm-ddThhmmss
    if not os.path.exists("backup/"):
        os.makedirs("backup/")
    newFile = "backup/{0}_raw_list.txt".format(datetime.now().strftime("%Y-%m-%dT%H%M%S"))
    copy2("raw_list.txt", newFile)
    print("Raw list backed up as "+newFile)

## main code execution ##
Completed = False
pageNum = 1
while not Completed:
    #grab page
    page = GrabPage(pageNum)
   # with open("pageData", "w") as p:
   #     p.write(page)
    print("Grabbed data for page {0}...".format(pageNum))
    #parse page and create new member list
    (newMembers, Completed) = ProcessPage(page)
    print("Processed member list for page {0}. {2} new members. Finished? {1}".format(pageNum, Completed, len(newMembers)))
    members += newMembers
    #increment the page number
    pageNum += 1

#Write the new member list
newMemberCount = FindNewMembers(members)

#write the raw member list to a file
SaveRawList()

#Back up list
BackUpRawList()

print("Applying descriptions...")
ProcessDescriptions()

for member in members:
    if not member.ignore:
        print("{0}:{1} color:{2}".format(member.username, member.TotalRep, member.color))

print("{0} total members!".format(len(members)))
print("{0} brand new members!".format(newMemberCount))
#write the member list to a file
SaveFinalList()
print("Finished!")

'''
The MIT License (MIT)

Copyright (c) 2017 Michael Marvin (magico13)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
'''
