import requests
from bs4 import BeautifulSoup as bs, Tag
import os
from PIL import Image
from pypdf import PdfMerger
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from tqdm import tqdm
import random
import string


# Generates random color code
def randomColorCode() -> str:
    # Chooses random hex digits from set of hex numbers and joins them
    colorCode : str = "".join(random.choices(string.hexdigits, k=6))
    # Adds hash symbol
    colorCode = "#" + colorCode
    return colorCode

# Function that searches for managa
def searchForManga(query : str) -> tuple:
    # Replaces spaces with "_"
    query = query.replace(" ","_")
    # Creates link
    link : str = f"https://manganato.com/search/story/{query}"
    # Creates new session
    session : requests.Session = requests.session()
    # Fetches the html data of the search page
    htmlData = session.get(link).text
    # Parses the data into a format we can look for tags in
    parsedData = bs(htmlData,"lxml")

    # Gets the div containing the search results
    resultsContainer : Tag = parsedData.find("div",{"class":"panel-search-story"})
    # Creates an empty dictionary
    resultsDict : dict[int:tuple] = {} 
    # Loops over search results
    for i,result in enumerate(resultsContainer.find_all("div",{"class":"search-story-item"})):
        # Gets the <a> tag containg the manga data
        aTag : Tag = result.find("a")
        # Prints the title and ID
        print(aTag.get("title"))
        print(f"ID: {i}")
        # Updates the dictionary with the new data
        resultsDict.update({i:(aTag.get("href"),aTag.get("title"))})
    
    # Will run until a valid input is given
    while True:
        try:
            # Gets the ID for the manga
            chosenID : int = int(input("Enter ID of manga: "))
            break
        except:
            print("Invalid input try again")
    # Returns the tuple of the link and name
    return resultsDict[chosenID]

def getLatestChapter(link : str) -> str:
    # Creates new session
    session : requests.Session = requests.session()
    # Fetches html data
    htmlData = session.get(link).text
    # Parses the data
    parsedData = bs(htmlData,"lxml")
    # Gets the chapters container
    chapCont : Tag = parsedData.find("div",{"class":"panel-story-chapter-list"})
    # Gets actual chapters container
    ulCont : Tag = chapCont.find("ul",{"class":"row-content-chapter"})
    # Latest chapter container
    lastestChapCont : Tag = ulCont.find_next("li",{"class":"a-h"})
    # <a> Tag containing the chapter info
    aTag : Tag = lastestChapCont.find("a")
    # returns chapter number
    return aTag.getText()

# Function that makes pdfs of the manga chapter 
def pdfize(_dir,name,chapter):
        # Alert of pdfing the chapter initialization
        print(f"Started pdfiziing chapter {chapter}")
        # Selects all image files in a directory acoording to certain parameters
        image_files = [f for f in os.listdir(_dir) if f.endswith('.jpg') or f.endswith('.jpeg') or f.endswith('.png')]

        # Creates a pdf canvas of letter size and name of the manga and its chapter
        pdf = canvas.Canvas(f'{_dir}/{name}-{chapter}.pdf', pagesize=letter)

        # Loops through all image files and creates a loading bar for it
        for i in tqdm(range(0,len(image_files)), colour=randomColorCode(), desc=f"Chapter {chapter}"):
            # Defines images path in numerical order
            image_path =f"{_dir}/{i}.jpg"
            # Opens the image file to be written in the pdf
            img = Image.open(image_path)
            # Calculate the scaling factor to fit the image within the PDF page
            # img.size is a tuple of (width,height)
            width, height = img.size
            # Gets the max size of the page
            max_width, max_height = letter
            # Scaling factor is the max dim / img dim,
            # We select the smallest so the other dimension gets displayed properly
            scaling_factor = min(max_width/width, max_height/height)

            # Scale the image size
            new_width = int(width * scaling_factor)
            new_height = int(height * scaling_factor)

            # Draw the image on the PDF canvas
            pdf.drawImage(image_path, 0, 0, width=new_width, height=new_height, preserveAspectRatio=True)

            # Check if its the last page
            # If its not we create a new page
            if i < len(image_files) - 1:
                pdf.showPage()
        # Saves the pdf file
        pdf.save()
        # Alerts the pdf is done
        print(f"Done pdfizing chapter {chapter}")


# Function to merge all pdf files of a manga into one pdf file
def mergePDFS(direc,name):
    # Finds all chapter direcetories 
    directiories = [d for d in os.listdir(direc) if os.path.isdir(os.path.join(direc,d))]
    # Makes an empty list where the pdf files will be
    pdfFiles = []
    # Loops through directories and finds all pdf files
    for dirr in directiories:
        for f in os.listdir(os.path.join(direc,dirr)):
            if f.endswith(".pdf"):
                pdfFiles.append(os.path.join(direc,os.path.join(dirr,f)))

    # Function that finds the numeric part of the pdf name
    def get_numeric_part(filename):
        return float(filename.split("-")[-1].replace(".pdf",""))

    # Sorts the pdf files according to the chapter number
    pdfFiles.sort(key=get_numeric_part)
    # Makes a pdf merger object
    merger = PdfMerger()
    # Loops through all files append them while displaying the progress in a progress bar
    for i in tqdm(range(len(pdfFiles)), colour=randomColorCode(),desc=f"{name}.pdf"):
        file = pdfFiles[i]
        merger.append(file)
    # Creates the file and closes the megrger object
    merger.write(f"./{name}.pdf")
    merger.close()


def getAllLinks(link : str,name : str) -> None:
    session = requests.session()
    text = session.get(link).text
    parsedData = bs(text,"lxml")
    chapList = parsedData.find("div",{"class":"panel-story-chapter-list"})
    chapters = list(chapList.find_all("li",{"class":"a-h"}))
    chapters.reverse()
    for i in range(len(chapters)):
        chapLink = chapters[i].find("a").get("href")
        chapNum = chapLink.split("-")[-1]
        save(chapLink,name,chapNum)
        pdfize(f"./{name}/{name}-{chapNum}",name,chapNum)

# Saves the chapter in the designated folder
def save(link: str,name: str,chapter: int):
    # Starts a new session
    sesh = requests.session()
    # Fetches the html data
    text = sesh.get(link).text
    # Soups the data so we can look through it
    text = bs(text,"lxml")
    # Gets the div where all the images are stored
    imgDiv = text.find("div",{"class":"container-chapter-reader"})
    # imgDiv = [div for div in text.find_all("div") if "reader" in str(div.get("class"))][0]
    # Gets all the image links
    imgs = [img.get("src") for img in imgDiv.find_all("img") if "page" in str(img.get("title"))]
    # Headers extracted manually from the website
    headers = {
        'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.7',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'Referer': 'https://chapmanganato.com/',
        'Sec-Ch-Ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Brave";v="114"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Linux"',
        'Sec-Fetch-Dest': 'image',
        'Sec-Fetch-Mode': 'no-cors',
        'Sec-Fetch-Site': 'cross-site',
        'Sec-Gpc': '1',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
    }
    # Creates a folder for the chapter under the parent manga folder
    try:
        os.mkdir(f"./{name}/{name}-{chapter}")
    except:
        print("Directory exists")
    # Loops through all images and shows progress in the progress bar
    for i in tqdm(range(0,len(imgs)), colour=randomColorCode(), desc=f"Chapter {chapter}"):
        if not os.path.exists(f"./{name}/{name}-{chapter}/{i}.jpg"):
            # Requests the files using the session and the extracted headers
            res = sesh.get(imgs[i],headers=headers)

            # If server response is OK we save the image
            if res.status_code == 200:
                # Reads the bytes from the response
                image_content = BytesIO(res.content)
                # Opens the bytes as an image
                image = Image.open(image_content)
                # Changes mode from P mode to RGB
                image = image.convert('RGB')
                # Saves the image in its designated directory
                image.save(f"./{name}/{name}-{chapter}/{i}.jpg")
            # If response isnt OK we log an error 
            else:
                print(res.status_code)
        else:
            print(f"Page {i} of chapter {chapter} exists, skipping...")


# Checks if link is a valid link
def isValidLink(link: str) -> bool:
    # Checks if the connection is secure
    if "https" not in link:
        return False
    # Checks if the link format is correct
    if link[len(link) - 1] == "/":
        return False
    # Splits link into parts
    linkSplit : list = link.split("/")
    # Checks if the correct domain is provided
    if "chapmanganato.com" not in linkSplit[2]:
        return False
    return True


# Deprecated main function
def mainDep():
    # Asks for user input of link
    link: str= input("Enter link: ")
    # Asks for chapter
    chapter: int = int(input("Enter chapter: "))
    # Creates link using provided data
    link = f"{link}/chapter-{chapter}"
    # Asks for manga name
    name: str = input("Enter name: ")
    # Saves the chapter
    save(link,name,chapter)
    # Makes a pdf of the chapter
    pdfize(f"./{name}-{chapter}",name,chapter)

def processLink(link : str) -> str:
    linkArr : list = link.split("/")
    return "https://chapmanganato.com/"+linkArr[-1]
# Working main function
def main():
    # Takes user input for search query
    linkMain, name = searchForManga(input("Enter manga name to search for: "))
    mangaLink : str = linkMain
    linkMain = processLink(linkMain)
    # Prints the latest chapter
    print(f"The latest chapter is: {getLatestChapter(linkMain)}")
    try:
        # Takes user input for start chapter
        chapterStart: int = int(input("Enter start chapter: "))
        # Takes user input for number of chapters
        numChapter: int = int(input("Enter number of chapters: "))
    except:
        # Exits if input isnt an integer
        print("Not an valid number, exiting...")
        exit(0)
    # Makes parent directory for managa
    try:
        os.mkdir(f"./{name}")
    except:
        print("Parent directory exists")

    if numChapter >= 99999:
        getAllLinks(mangaLink,name)
    else:
        # Loops through all chapter
        for i in  list(range(chapterStart,chapterStart+numChapter)):
            # Defines chapter as the current index
            chapter = i
            # Define link using given chapter
            link = f"{linkMain}/chapter-{chapter}"
            # Logs the start of saving
            print(f"Saving chapter {chapter}")
            # Saves given chapter
            save(link,name,chapter)
            print("\n")
            # Creates pdf of the chapter
            pdfize(f"./{name}/{name}-{chapter}",name,chapter)
            print("\n")
        # Logs the start of merging the pdfs
        print("Started merging")
        # Starts merging
    mergePDFS(f"./{name}",name)
    
# Runs if the script is used directly and not as an import
if __name__ == '__main__':
    main()
