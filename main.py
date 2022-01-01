import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def main():
    YOUTUBE_URL = "http://www.youtube.com"
    source_file = None
    video_titles = []
    video_links = []

    print(">> Welcome to youtube_dl_helper!")

    while not source_file:
        print(">> Please enter source file path:")
        source_file_path = input("-- ")

        try:
            source_file = open(source_file_path, "r")
        except:
            print(">> Error opening '" + source_file_path + "'! Please try again!")


    print(">> Parsing " + source_file_path + "...")

    for title in source_file: # Reads textfile line by line
        if title != '\n' and '//' not in title:
            video_titles.append(title[:-1]) # Stores content of each line, minus \n character
                                            # Lines that contain a // are considered a comment, and are ignored

    track_count = len(video_titles)

    print(">> " + str(track_count) + " track titles parsed from " + source_file_path)


    driver = webdriver.Chrome(service = Service(ChromeDriverManager().install()))
    driver.maximize_window()

    wait = WebDriverWait(driver, 3)
    presence = EC.presence_of_element_located
    visible = EC.visibility_of_element_located

    print("\n>> Gathering track URIs...")

    current_track_number = 1
    for title in video_titles:
        print(">> Storing URI [" + str(current_track_number) + " of " + str(track_count) + "]...")

        driver.get(YOUTUBE_URL + "/results?search_query=" + title)
        assert "YouTube" in driver.title
        assert "No results found" not in driver.page_source
        wait.until(visible((By.ID, "video-title")))
        href = driver.find_element(By.ID, "video-title").get_attribute("href")
        video_links.append(href)

        current_track_number += 1

    driver.quit()

    if os.name == "nt":
        os.system("if not exist audio_files\\NUL mkdir audio_files\\")
    else:
        os.system("if [ ! -d audio_files/ ] ; then mkdir audio_files; fi  ")

    print(">> URIs ready! Starting downloads...")

    current_track_number = 1
    for title, link in zip(video_titles, video_links):
        print(">> Downloading track [" + str(current_track_number) + " of " + str(track_count) + "]...")

        try:
            os.system('youtube-dl -o "audio_files/' + title + '.%(ext)s" --rm-cache-dir --extract-audio --audio-format mp3 ' + link)
        except:
            pass

        current_track_number += 1

    print(">> Process Complete!")

    source_file.close()


if __name__ == "__main__":
    main()
