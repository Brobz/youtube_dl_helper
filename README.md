# youtube_dl_helper

A helper program meant to automate the process of downloading mp3 files from YouTube using youtube-dl library, as well as setting the file's metadata according to a self-made syntaxis from a source "track list" text file.

## Dependencies

In order to run _youtube_dl_helper_, you will need (apart from python, obviously):

- selenium
- youtube-dl
- ffmpeg
- eyeD3

All of these dependencies can be acquired for free from the web, by using services like ```pip```, ```brew``` or ```choco```

## Usage:

1. Create a text file containing desired track titles, one per line (// will denote the line as a comment, and it will be ignored!)
2. Run ```python main.py``` and pass in your ```.txt``` file path
3. Wait for the automated process to unfold...
4. Enjoy your freshly downloaded mp3 files!


### Note

An example track list text file (with all is syntactic flairs for metadata parsing) can be found on this very repository, under _example_track_list.txt_
