# ----- Imports -------
import os
import pytube
import ffmpeg
import keyboard
from tkinter import filedialog, Tk
from urllib.error import URLError

# ------- Functions ----------

def get_clear_command():
    '''
        Gets the clear command for the terminal based on platform.

        Arguments:
        No arguments

        Return:
        String -> Command to clear the terminal.
    '''

    if os.name == "nt":
        return "cls"
    
    return "clear"




def download_video(filedir, yt, resolution="720p", mode="search"):
    '''
        Downloads the video and audio files to be merged later.
        
        Arguments:
        filedir -- Directory path where the files should be downloaded.
        yt -- Youtube object provided by pytube module.

        Return:
        A tuple containing names of video and audio files.
        
    '''
    if mode=="search":
        available_qualities = set()

        for labels in yt.streams.filter(only_video=True):
            available_qualities.add(int(labels.resolution[0:-1]))

        available_qualities = list(sorted(available_qualities))

        i = 1
        print()
        for quality in available_qualities:
            print(f"{i} - {quality}p")
            i+=1
        choice = input(f"Select a quality (1-{i-1}): ")
        stream = yt.streams.filter(file_extension="mp4", only_video=True, res=f"{str(available_qualities[int(choice)-1])}p")
        print("Downloading...")
        stream[0].download(output_path=filedir)
    
    elif mode=="batch":
        stream = yt.streams.filter(file_extension="mp4", only_video=True, res=resolution)
        print("Downloading...")
        stream[0].download(output_path=filedir)
    
    else:
        raise Exception("Invalid mode entered as parameter.")
    
    audio_stream = yt.streams.get_audio_only()
    audio_stream.download(output_path=filedir, filename=f"{audio_stream.default_filename[0:-4]}_audio.mp4")

    return (stream[0].default_filename, f"{audio_stream.default_filename[0:-4]}_audio.mp4")


def merge_video_and_audio(filedir, video_audio):
    '''
        Merge the video and audio files into a single file.
        
        Arguments:
        filedir -- Directory path where the files should be downloaded.
        video_audio -- Tuple containing video and audio files.

        Return:
        None
        
    '''

    stream, audio_stream = video_audio
    
    input_video = ffmpeg.input(f"{filedir}/{stream}")
    input_audio = ffmpeg.input(f"{filedir}/{audio_stream}")

    out = ffmpeg.concat(input_video, input_audio, v=1, a=1).output(f"{filedir}/{stream[0:-4]}_out.mp4")
    out.run()
    os.remove(f"{filedir}/{stream}")
    os.remove(f"{filedir}/{audio_stream}")
    os.rename(f"{filedir}/{stream[0:-4]}_out.mp4", f"{filedir}/{stream}")
    
    return None

def download_audio(filedir, yt):
    '''
        Downloads the audio file.
        
        Arguments:
        filedir -- Directory path where the files should be downloaded.
        yt -- Youtube object provided by pytube module

        Return:
        Name of the audio file.
        
    '''

    available_qualities = set()
    
    for stream in yt.streams.filter(only_audio=True):
            available_qualities.add(int(stream.abr[0:-4]))
    
    available_qualities = list(sorted(available_qualities))

    i = 1
    print()
    for quality in available_qualities:
        print(f"{i} - {quality}kbps")
        i+=1
    
    choice = input(f"Select a bitrate (1-{i-1}): ")
    stream = yt.streams.filter(only_audio=True, abr=f"{str(available_qualities[int(choice)-1])}kbps")
    stream[0].download(output_path=filedir, filename=f"{stream[0].default_filename[0:-4]}_audio.mp4")
    return f"{stream[0].default_filename[0:-4]}_audio.mp4"



def convert_audio_to_mp3(filedir, audio_stream):
    '''
        Converts the audio file to mp3.
        
        Arguments:
        filedir -- Directory path where the files should be downloaded.
        audio_stream -- Name of the audio file.

        Return:
        None
        
    '''

    audio = ffmpeg.input(f"{filedir}/{audio_stream}")
    out = audio.output(f"{filedir}/{audio_stream[0:-4]}_out.mp3", f='mp3')
    out.run()
    os.remove(f"{filedir}/{audio_stream}")
    os.rename(f"{filedir}/{audio_stream[0:-4]}_out.mp3", f"{filedir}/{audio_stream[0:-10]}.mp3")
    
    return None 


def get_download_dir():
    '''
        Gets the directory path to download the files into.
        
        Arguments:
        No arguments

        Return:
        Directory path
        
    '''
    root = Tk()
    root.withdraw()
    root.focus_force() 

    currdir = os.getcwd()
    return filedialog.askdirectory(parent=root, initialdir=currdir, title='Please select a directory')


def search_video_or_audio():
        '''
            Performs search for the video or audio on Youtube

            Arguments:
            No arguments

            Return:
            None
        '''
        query = input("Enter the name of video to search: ")

        # Intialize the search object.
        s = pytube.Search(query)

        i = 1
        print()
        for result in s.results:
            print(f"{i} - {result.title} | {result.author}")
            i+=1


        choice = input(f"Select the video you want to download (1-{i-1}): ")

        #  Select a Youtube object
        yt = s.results[int(choice)-1]

        # Select a directory to download files into.
        print("Please select a directory/folder to download the files into.")
        filedir = get_download_dir()
        
        # Choose video(with audio) or audio only.
        choice = input(f"\nDo you want video or audio: ")

        if choice.lower() == "video":
            
            # In case of video, download and merge the video and audio files.
            video_and_audio = download_video(filedir, yt)
        
            merge_video_and_audio(filedir, video_and_audio)

        elif choice.lower() == "audio":
            
            # In case of audio, download and convert the audio file.
            
            print("Downloading...")
            audio_stream = download_audio(filedir, yt)
            
            convert_audio_to_mp3(filedir, audio_stream)
        else:
            print("Invalid option selected.")
            return 1
        
        return None

def batch_download():
    '''
        Batch downloads the videos from the links provided in the selected text file.

        Arguments:
        No arguments

        Return:
        None
    '''

    resolutions = ["1080p", "720p", "480p", "360p", "240", "144p"]
    
    print("Please select a directory/folder to download the files into.")
    filedir = get_download_dir()
    print("Please select the text file containing the Youtube video links")
    file = filedialog.askopenfile(initialdir=os.getcwd())
    
    if file==None:
        print("No file selected. Please select a file.")
        return 1
    
    # Resolution selection for videos in the batch.
    print("Resolution Selection: \n1. 1080p\n2. 720p\n3. 480p\n4. 360p\n5. 240p\n6. 144p\n\n")
    resolution = input("Select a resolution(1-6): ")
    
    # Downloads the video for every link.
    for link in file.readlines():

        #Initializes Youtube object.
        yt = pytube.YouTube(link)
        
        print("Downloading...")
        #Downloads the video and audio files and returns their names.
        video_and_audio = download_video(filedir, yt, resolutions[int(resolution)-1], "batch")
        
        #Merges the video and audio files.
        merge_video_and_audio(filedir, video_and_audio)
    
    return None
    



### Downloader code

os.system(get_clear_command())
print("----Welcome to the Youtube Downloader----",)
print("\nPress the Esc key at any time to exit.")
print("\n\nPress the Enter key to continue.")

# Exit when escape key is pressed.
keyboard.add_hotkey('esc', lambda:  os.abort())
keyboard.wait('enter', suppress=True)

os.system(get_clear_command())

try:
    while(True):

        # Exit when escape key is pressed.
        keyboard.add_hotkey('esc', lambda:  os.abort())
        
        ch = input("----Mode Selection---\n1. Batch Download\n2. Search\nPress the Esc key to exit.\nPlease select a mode(1-2): ")
        
        if ch=="1":
            print("---INSTRUCTIONS---\nPut all the links of Youtube videos in a text file.\nThere should be only 1 link on each line.\n\n")
            input("Press enter when you're ready.")
            error = batch_download()
            if error!=None:
                continue
        elif ch=="2":
            error = search_video_or_audio()
            if error!=None:
                continue
        else:
            print("Invalid option selected")
            continue

        os.system(get_clear_command())
        print("Download Completed!")

except URLError:
    print("Please check your internet connection")

except KeyError:
    print("Cannot find the video or the video is age restricted")