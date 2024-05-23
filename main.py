import os, time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.remote_connection import LOGGER, logging


"""
Changelog

- 23/05/2024
    Did need to refactor.
    Now uses yt-dlp instead of youtube-dl.
    Metada application is now flimsy since yt-dlp continues code execution before the file can finish downloading.
    Need to figure out a fix.

- 22/05/2024
    So, apparently, according to results from brew install youtube-dl:

        The current youtube-dl version has many unresolved issues.
        Upstream have not tagged a new release since 2021.

        Please use yt-dlp instead.

    Might need to refactor this whole thing? Need to check.
"""

def main():
    YOUTUBE_URL = "http://www.youtube.com"
    source_file = None
    video_titles = []
    video_links = []
    track_metadata = []

    print(">> Welcome to youtube_dl_helper!")

    while not source_file:
        print(">> Please enter source file path:")
        source_file_path = input("-- ")

        try:
            source_file = open(source_file_path, "r")
        except:
            print(">> Error opening '" + source_file_path + "'! Please try again!")

    print(">> WARNING: Current version of yt-dlp does not wait for download to complete before returning a success signal to os.system()")
    print(">> WARNING: Skipping metadata step is recommended until I figure a way to fix this")
    print(">> WARNING: Apply metada (at risk of failure)? (Y/N)")

    apply_metadata_flag = input("-- ")

    print(">> Parsing " + source_file_path + "...")

    for line in source_file: # Reads textfile line by line
        if line != '\n' and '//' not in line: # we will be parsing this line (its neither an empty line nor a comment)

            if '||' not in line: # this is a simple no-metadata line that only contains search name / file name parameter
                video_titles.append(line[:-1])  # Stores content of each line, minus \n character
                                                # Lines that contain a // are considered a comment, and are ignored
                track_metadata.append([None, None, None]) # Store all Nones for empty metadata
                continue

            # at this point, we know we are messing with some metadata
            # now lets check for that convenient - separator syntax
            res = '-' in line
            if res:
                # we have it!
                res = line.index('-')
                if res >= 0:
                    # no '-' in artist title allowed, they wil always split artist title and track title
                    track_metadata.append([line[:res - 1], line[line.find("||") + 3:-1], line[res + 2: line.find("||") - 1]])
                    # grab the search name and store it
                    video_titles.append(line[:line.find('||') - 1])
                    continue

            # we don't have it! we'll do it the hard way then
            metadata = [None, None, None]

            # first, grab the search name and store it
            video_titles.append(line[:line.find('||') - 1])

            # now fill the rest of the metadata
            line = line[line.find('||') + 3:]
            artist = line[:line.index('||') - 1]
            if artist != "NULL":
                metadata[0] = artist

            line = line[line.index('||') + 3:]
            album = line[:line.index('||') - 1]
            if album != "NULL":
                metadata[1] = album

            line = line[line.index('||') + 3:]
            track_title = line[:-1]
            if track_title != "NULL":
                metadata[2] = track_title

            # punch it in
            track_metadata.append(metadata)

    source_file.close() # Close source file; We won't be needing it anymore

    track_count = len(video_titles)

    print(">> Done! [" + str(track_count) + "] tracks parsed from " + source_file_path)

    print(">> Starting Chrome WebDriver...")

    LOGGER.setLevel(logging.WARNING) # Reduces verbosity of ChromeWebDriver

    driver = webdriver.Chrome(service = Service(ChromeDriverManager().install()))
    driver.maximize_window()

    wait = WebDriverWait(driver, 3)
    presence = EC.presence_of_element_located
    visible = EC.visibility_of_element_located

    print("\n>> Gathering track URIs...")

    current_track_number = 1
    for title in video_titles:
        # before trying to download using title, we need to clean it up a bit
        # by escaping any ' that are present with a \
        res = "'" in title
        while res:
            res = False
            for i, char in enumerate(title):
                if char == "'" and title[i - 1] != "\\":
                    title = title[:i] + "\\" + title[i:]
                    res = True
                    break

        print(">> Storing URI [" + str(current_track_number) + " of " + str(track_count) + "]...")

        driver.get(YOUTUBE_URL + "/results?search_query=" + title)

        wait.until(visible((By.ID, "video-title")))

        assert "YouTube" in driver.title
        assert "No results found" not in driver.page_source
        
        href = driver.find_element(By.ID, "video-title").get_attribute("href")
        video_links.append(href)

        current_track_number += 1

    driver.quit()

    if os.name == "nt":
        os.system("if not exist audio_files\\NUL mkdir audio_files\\")
    else:
        os.system("if [ ! -d audio_files/ ] ; then mkdir audio_files; fi  ")

    print(">> URIs ready! Starting downloads...")

    current_track_number = 0
    for title, link in zip(video_titles, video_links):
        current_track_number += 1
        print(">> Downloading track [" + str(current_track_number) + " of " + str(track_count) + "]...")
        try:
            # replace any ( or ) in track title with [] to avoid bash errors
            # also replacing any spaces with _, just for good measure
            title = title.replace("(", "[")
            title = title.replace(")", "]")
            title = title.replace(" ", "_")

            # --rm-cache-dir flag prevents weird 403 HTTP errors from happening
            download_cmd = 'yt-dlp --rm-cache-dir -x --audio-format mp3 -o "audio_files/' + title + '.mp3" ' + link
            
            # First, write command into temp bash file so that os.system() actually waits for it to finish
            temp_sh_filename = "temp_cmd.sh"
            os.system("touch " + temp_sh_filename)
            os.system("> " + temp_sh_filename)
            os.system('echo "' + download_cmd + '" >> ' + temp_sh_filename)
            os.system("chmod +x " + temp_sh_filename)

            # Run the shell script
            res = os.system("sh " + temp_sh_filename)
        except Exception as e:
            print(e)
            # // TODO: maybe do some sort of recovery here? (loop back and try again a couple of times? maybe loop back at the end of the tracklist?)
            print(">> ERROR downloading track [" + str(current_track_number) + " of " + str(track_count) + "] !!! Skipping to next track...")
            continue

        if res:
            # res == 1 means an error during download operation
            # // TODO: maybe do some sort of recovery here? (loop back and try again a couple of times? maybe loop back at the end of the tracklist?)
            print(">> ERROR downloading track [" + str(current_track_number) + " of " + str(track_count) + "] !!! Skipping to next track...")
            continue
        

        if (apply_metadata_flag not in ["Y, Ye, Yes, y, ye, yes"]):
            print(">> Skipping metadata application...")
            continue

        # res == 0 means a successfull download operation
        # Since all went well for this track, all that is left to do
        # is set this file's metadata (if any is specified)
        current_track_metadata = track_metadata[current_track_number - 1]
        if current_track_metadata == [None, None, None]:
            # no metadata, move on to the next track
            continue

        print(">> Applying file metadata to track [" + str(current_track_number) + " of " + str(track_count) + "]...")
        # at least some metadata; grab it
        artist_metadata = current_track_metadata[0]
        album_title_metadata = current_track_metadata[1]
        track_title_metadata = current_track_metadata[2]

        # now apply it
        metadata_command =  'eyeD3 -Q' # -Q arg turns on "quiet" mode (less verbose output)
        if artist_metadata != None:
            metadata_command +=  ' -a "' + artist_metadata + '" --text-frame=TPE2:"' + artist_metadata + '"'
        if album_title_metadata != None:
            metadata_command += ' -A "' + album_title_metadata + '"'
        if track_title_metadata != None:
            metadata_command += ' -t "' + track_title_metadata + '"'

        metadata_command += ' "audio_files/' + title + '.mp3"'

        res = os.system(metadata_command)

    # All done!
    # Clean up temp shell script
    os.system("rm " + temp_sh_filename)

    print(">> Process Complete!")
    print(">> WARNING: Well, kind of. Downloads might still be going on in the background.")
    print(">> WARNING: Please make sure files are completely downloaded before closing this window.")

if __name__ == "__main__":
    main()
