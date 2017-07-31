#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PIL import Image
import os
import sys
import datetime
import zipfile
import shutil


maxPreviewWidth = 320
maxPreviewHeight = 320
maxImageWidth = 1280
maxImageHeight = 1024
jqueryfilename = "jquery.min.js"
moviethumbnail = "Movie-file-thumbnail.png"

knownExtensions = ["jpg", "jpeg", "gif", "png"]
movieFiles = ["mov", "mp4"]
indexfilename = "index.html"
thumbnailfoldername = "thumbnails"
previewfoldername = "preview"

html_escape_table = {
  "&": "&amp;",
  '"': "&quot;",
  "'": "&apos;",
  ">": "&gt;",
  "<": "&lt;"
}

def html_escape(text):
    return "".join(html_escape_table.get(c, c) for c in text)


def loadLanguageFile(languagecode):
    result = {}
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'language-' + languagecode + '.txt'), 'r', encoding='utf8') as languagefile:
        for line in languagefile:
            line = line.strip()
            if len(line) == 0:
                continue

            pos = line.index(' ')
            if pos != -1:
                result[line[0:pos]] = line[pos+1:]

    return result


def readTitles(filename):
    result = {}
    with open(filename, 'r', encoding='utf8') as titlefile:
        thefile = None
        thetitle = None
        for line in titlefile:
            line = line.strip()
            if len(line) == 0:
                if thefile is not None and thetitle is not None:
                    result[thefile] = thetitle
                thefile = None
                thetitle = None
            else:
                if thefile is None:
                    thefile = line.lower()
                else:
                    if thetitle is None:
                        thetitle = html_escape(line)
                    else:
                        thetitle = thetitle + "\n" + html_escape(line)

        if thefile is not None and thetitle is not None:
            result[thefile] = thetitle

    return result


#def doCopy(fromFile, toFile):
#    with open(fromFile, "rb") as fileorigin:
#        with open(toFile, "wb") as filedestination:
#            filedestination.write(fileorigin.read())


def doResize(im, maxWidth, maxHeight, resultFilename):
    resizeX = im.width
    resizeY = im.height
    resizeImage = False
    if im.width - maxWidth < im.height - maxHeight:
        if im.height > maxHeight:
            resizeY = maxHeight
            resizeX = int(im.width * (maxHeight / im.height))
            resizeImage = True
    else:
        if im.width > maxWidth:
            resizeX = maxWidth
            resizeY = int(im.height * (maxWidth / im.width))
            resizeImage = True

    if resizeImage:
        im = im.resize((resizeX, resizeY))

    im.save(resultFilename)


def createStorybook(folder, recursive, parent=None, languageCode='en'):
    languageStrings = loadLanguageFile(languageCode)

    if folder.endswith("/"):
        folder = folder[0:len(folder)-1]
    thePath = os.path.basename(folder)
    #storybookDir = os.path.join(os.path.abspath(os.path.join(folder, os.pardir)), thePath + "-storybook")
    storybookDir = thePath + "-storybook"
    _createStorybook(storybookDir, thePath, folder, recursive, parent, languageStrings, 0)


def _createStorybook(storybookDir, thePath, folder, recursive, parent, languageStrings, depth):
    global previewSize, knownExtensions, movieFiles, indexfilename, thumbnailfoldername, previewfoldername, jqueryfilename, moviethumbnail
    filesConsidered = False

    if not os.path.exists(storybookDir):
        os.mkdir(storybookDir)
    theThumbnailFolder = os.path.join(storybookDir, thumbnailfoldername)
    if not os.path.exists(theThumbnailFolder):
        os.mkdir(theThumbnailFolder)

    thePreviewFolder = os.path.join(storybookDir, previewfoldername)
    if not os.path.exists(thePreviewFolder):
        os.mkdir(thePreviewFolder)

    thehtml = ""
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "storybook-html.txt"), 'r', encoding='utf-8') as storybookfile:
        thehtml = storybookfile.read()

    titles = {}
    titlefile = os.path.join(folder, "index.txt")
    if os.path.exists(titlefile):
        titles = readTitles(titlefile)

    if depth == 0:
        shutil.copy(os.path.join(os.path.dirname(os.path.realpath(__file__)), jqueryfilename), os.path.join(storybookDir, jqueryfilename))
        shutil.copy(os.path.join(os.path.dirname(os.path.realpath(__file__)), moviethumbnail), os.path.join(storybookDir, moviethumbnail))
    imagesDict = {}
    childDirs = []
    archiveName = os.path.basename(folder) + ".zip"
    archive = None
    for subdir, dirs, files in os.walk(folder):

        for file in files:
            extensionPos = file.rfind(".")
            extension = None
            if extensionPos != -1:
                extension = file[extensionPos+1:].lower()
            if extension is None or (extension not in knownExtensions and extension not in movieFiles):
                print("WARNING: ignoring file " + os.path.join(folder, file))
                continue

            print("adding " + os.path.join(folder, file))
            filesConsidered = True
            renamedFile = file.encode('ascii', errors='ignore').decode()
            if renamedFile != file:
                os.rename(os.path.join(folder, file), os.path.join(folder, renamedFile))
                print("WARNING: renamed file " + folder + "/" + file)
                file = renamedFile

            if archive is None:
                archive = zipfile.ZipFile(os.path.join(storybookDir, archiveName), "w")
            archive.write(os.path.join(folder, file), os.path.join(thePath, file))

            currentFile = os.path.join(folder, file)
            thePreviewFile = os.path.join(thePreviewFolder, file)

            if extension in movieFiles:
                timestamp = datetime.datetime.fromtimestamp(os.path.getmtime(os.path.join(folder, file)))
                shutil.copy(currentFile, thePreviewFile)
            else:
                im = Image.open(currentFile)

                exifInfo = None
                if hasattr(im, '_getexif'):
                    exifInfo = im._getexif()
                    if exifInfo is not None:
                        if 274 in exifInfo:
                            if exifInfo[274] == 3:
                                im = im.rotate(180, expand=True)
                                print("INFO: image rotated")
                            elif exifInfo[274] == 6:
                                im = im.rotate(270, expand=True)
                                print("INFO: image rotated")
                            elif exifInfo[274] == 8:
                                im = im.rotate(90, expand=True)
                                print("INFO: image rotated")

                theThumbnailFile = os.path.join(theThumbnailFolder, file)
                doResize(im, maxPreviewWidth, maxPreviewHeight, theThumbnailFile)

                doResize(im, maxImageWidth, maxImageHeight, thePreviewFile)

                timestamp = None
                if exifInfo is not None and 36867 in exifInfo and exifInfo[36867].strip() != "":
                    timestamp = datetime.datetime.strptime(exifInfo[36867], "%Y:%m:%d %H:%M:%S")
                else:
                    timestamp = datetime.datetime.fromtimestamp(os.path.getmtime(os.path.join(folder, file)))


            timestampString = timestamp.strftime("%Y-%m-%d")
            timeString = timestamp.strftime("%H:%M:%S")
            if timestampString not in imagesDict:
                imagesDict[timestampString] = []

            thetitle = timeString
            showtitle = None
            if file.lower() in titles:
                thetitle = titles[file.lower()].replace("\n", " ") + " (" + timeString + ")"
                showtitle = titles[file.lower()].replace("\n", "<br>")

            imagesDict[timestampString].append({"file": file, "extension": extension, "timeString": timeString, "title": thetitle, "showtitle": showtitle})

        childDirs = dirs
        break

    if archive is not None:
        archive.close()

    childDirsConsidered = []
    for childDir in childDirs:
        if recursive:
            storybookDirChild = os.path.join(storybookDir, childDir)
            childFilesConsidered = _createStorybook(storybookDirChild, thePath + "/" + childDir, os.path.join(folder, childDir), True, folder, languageStrings, depth + 1)
            if childFilesConsidered:
                childDirsConsidered.append(childDir)
            else:
                print("WARNING: no files considered in folder " + os.path.join(folder, childDir))
        else:
            print("WARNING: ignoring folder " + os.path.join(folder, childDir))

    content = ""
    if archive is not None:
        content = content + "<div class=\"card\" style=\"text-align:right\"><a href=\"" + archiveName + "\">%T_DOWNLOAD_THIS_FOLDER%</a></div>"

    if recursive and (parent is not None or len(childDirsConsidered) > 0):
        content = content + "<div class=\"card\">%T_FOLDER_CONTENTS%:<br><ul>"
        if parent is not None:
            content = content + "<li><a href=\"../index.html\">[%T_PARENT_DIR%]</a></li>\n"
        for childDirConsidered in childDirsConsidered:
            content = content + "<li><a href=\"" + childDirConsidered + "/index.html\">" + childDirConsidered + "</a></li>\n"
        content = content + "</ul></div>\n"

    for key, value in sorted(imagesDict.items()):
        content = content + "\n<div class=\"card\">" + key + "<br>\n"
        for image in sorted(value, key=lambda yx: yx["timeString"]):
            showtitle = ""
            showtitleclass = ""
            if image["showtitle"] is not None:
                showtitle = " showtitle=\"" + image["showtitle"] + "\""
                showtitleclass = " showtitle"
            if image["extension"] in movieFiles:
                content = content + "<img class=\"thumb movie" + showtitleclass + "\"" + showtitle + " title=\"" + image["title"] + "\" src=\"" + ("../"*depth) + moviethumbnail + "\" themovie=\"" + image["file"] + "\">\n"
            else:
                content = content + "<img class=\"thumb" + showtitleclass + "\"" + showtitle + " title=\"" + image["title"] + "\" src=\"" + thumbnailfoldername + "/" + image["file"] + "\">\n"
        content = content + "</div>\n"

    thehtml = thehtml.replace("%RELATIVE_PATH%", "../"*depth)
    thehtml = thehtml.replace("%TITLE%", thePath)
    thehtml = thehtml.replace("%CONTENT%", content)
    for languageKey, languageValue in languageStrings.items():
        thehtml = thehtml.replace(languageKey, languageValue)
    with open(os.path.join(storybookDir, indexfilename), 'w', encoding='utf8') as indexfile:
        indexfile.write(thehtml)

    return filesConsidered


if __name__ == "__main__":
    thefolder = sys.argv[1]
    #print("Please specify folder: ")
    #thefolder = input()
    languageCode = 'en'

    createStorybook(thefolder, True, None, languageCode)

