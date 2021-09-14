import datetime
import requests
import os
import re
import pytube
import subprocess
from pytube import YouTube
import streamlit as st
from PIL import Image
from io import BytesIO

def show_download_button(filepath, mime, filename='downloaded'):
    data = open(filepath, 'rb')
    st.download_button('Get File', data=data, mime=mime, file_name=filename)

def getVideo(url): #Check to ensure that the video can be found
    global video_found, video
    try:
        video = YouTube(url)
        video_found = True
    except pytube.exceptions.RegexMatchError:
        st.error('Invalid URL.')
        video_found = False
    except pytube.exceptions.VideoUnavailable:
        st.error('This video is unavailable')
        video_found = False
    return video

def loadThumbnail(image_url):
    response = requests.get(image_url)
    img = Image.open(BytesIO(response.content))
    return img

@st.cache
def getStats(video): # Return the formated video stats
    header = (f'**{video.title}**' 
            + f' *By: {video.author}*')
    thumbnail = loadThumbnail(video.thumbnail_url)
    info = (f'Length: **{datetime.timedelta(seconds = video.length)}** \n'
          + f'Views: **{video.views:,}**')
    return header, thumbnail, info

st.title('YouTube Downloader')

url = st.text_input('Enter the URL of the YouTube video')

if url:
    video = getVideo(url)
    if video_found:
        header, thumbnail, info = getStats(video)
        st.header(header)
        st.image(thumbnail, width = 750)
        st.write(info)
        download_type = st.radio(
        'Select the type of download you would like', [
        'Video (.mkv)', 
        'Audio Only (.mp3)']
        )

        if download_type == 'Video (.mkv)':
            try:
                os.remove('Downloads/downloaded.mkv')
            except:
                pass

            video_stream = video.streams.filter(type = 'video', subtype = 'mp4').order_by(attribute_name = 'resolution').last()
            audio_stream = video.streams.get_audio_only()
            filesize = round((video_stream.filesize + audio_stream.filesize)/1000000, 2)
            if st.button(f'Download (~{filesize} MB)'): 
            # To get the highest resolution, the audio and video streams must be installed seperate as .mp4s,
            # so the audio track must be converted to an mp3, then merged with the video, then the other files must be deleted
                with st.spinner(
                 f'Downloading {video.title}... ***Please wait to open any files until the download has finished***'
                ):
                    video_stream.download(filename = 'video-track.mp4')
                    audio_stream.download(filename = 'audio-track.mp3')
                    convert_mp3 = 'ffmpeg -i audio-track.mp4 audio-track.mp3'
                    subprocess.run(convert_mp3, shell = False)
                    formatted_title = 'downloaded'
                    merge_audio_video = (
                                         'ffmpeg -y -i audio-track.mp3 '
                                         '-r 30 -i video-track.mp4 '
                                         '-filter:a aresample=async=1 -c:a flac -c:v '
                                        f'copy Downloads/{formatted_title}.mkv'
                                          )
                    subprocess.run(merge_audio_video, shell = True)
                    os.remove('audio-track.mp3')
                    os.remove('video-track.mp4')
                    if show_download_button('Downloads/downloaded.mkv', 'video/x-matroska', filename='downloaded.mkv'):
                        st.success(f'Finished Downloading {video.title}!')

        elif download_type == 'Audio Only (.mp3)':
            try:
                os.remove('Downloads/downloaded.mp3')
            except:
                pass

            stream = video.streams.get_audio_only()
            filesize = round(stream.filesize/1000000, 2)
            if st.button(f'Download (~{filesize} MB)'):
                with st.spinner(
                 f'Downloading {video.title}... ***Please wait to open any files until the download has finished***'
                ):
                    stream.download(filename = 'audio')
                    convert_mp3 = f'ffmpeg -i audio Downloads/downloaded.mp3'
                    subprocess.run(convert_mp3, shell = True)
                    os.remove('audio')
                    if show_download_button('Downloads/downloaded.mp3', 'audio/mpeg', filename='downloaded.mp3'):
                        st.success(f'Finished Downloading {video.title}!')