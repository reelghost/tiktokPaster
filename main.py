import ffmpeg
import requests
import shutil
import os
import urllib
import json
from time import sleep
from TikTokUploader.uploader import uploadVideo

'''
Download video from tiktok and remove audio
take that video again and add audio synchronizing them
'''


def download_tiktok_audio(url):
    try:
        endpoint = f'https://tikwm.com/api/?url={url}'
        
        response = requests.get(endpoint)
        if not response.ok:
            raise Exception(f"Server returned Error code: {response.status_code} {response.reason}")
        
        data = response.json()
        if data and data['code'] == 0:
            music_url = data['data']['music']

            # download audio
            music_name = url.split('/video/')[-1]
            current_script_directory = os.path.dirname(os.path.abspath(__file__))
            file_path = f"{current_script_directory}/{music_name}.mp4"
            urllib.request.urlretrieve(music_url, file_path)
        
            print(f'Audio downloaded successfully as {music_name}')
        else:
            raise Exception("Failed to fetch audio")
    except Exception as e:
        print("Error occurred:", str(e))
    return file_path


def get_id_video(url):
    matching = "/video/" in url
    if not matching:
        print("[X] Error: URL not found")
        exit()
    id_video = url[url.index("/video/") + 7:]
    id_video = id_video.split('?')[0] if len(id_video) > 19 else id_video
    return id_video

def get_video(url):
    id_video = get_id_video(url)
    API_URL = f"https://api16-normal-c-useast1a.tiktokv.com/aweme/v1/feed/?aweme_id={id_video}"
    headers = {"Content-Type": "application/json"}  # Assuming headers are defined somewhere

    response = requests.get(API_URL, headers=headers)

    if response.status_code == 200:
        body = response.text
        try:
            res = json.loads(body)
        except Exception as err:
            print("Error:", err)
            print("Response body:", body)
            return None

        url_media = res['aweme_list'][0]['video']['play_addr']['url_list'][0]
        # download video
        current_script_directory = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_script_directory, f"{id_video}.mp4")
        urllib.request.urlretrieve(url_media, file_path)
        message = "[+]Video downloaded successfully..."
    else:
        message = f"Error: {response.status_code} - {response.reason}"
    return file_path


def remove_audio(video_file):
    try:
        output_file = f"no_{video_file}"
        
        # Run ffmpeg command to remove audio
        ffmpeg.input(video_file).output(output_file, **{'c:v': 'copy', 'an': None}).run()
        
        print(f"Audio removed from {video_file}. Output file: {output_file}")
        return output_file
    except ffmpeg.Error as e:
        print(f"Error occurred: {e.stderr}")
        return None



def add_audio_to_video(audio_file, video_file):
    try:
        # Get durations of audio and video files
        audio_info = ffmpeg.probe(audio_file)
        audio_duration = float(audio_info['format']['duration'])

        video_info = ffmpeg.probe(video_file)
        video_duration = float(video_info['format']['duration'])

        # Determine the duration to trim the audio
        duration_diff = video_duration - audio_duration
        if duration_diff > 0:
            # Trim audio to match video duration
            input_audio = ffmpeg.input(audio_file).audio.filter('atrim', duration=video_duration)
        else:
            # Trim video to match audio duration
            input_video = ffmpeg.input(video_file).video.filter('trim', duration=audio_duration)

        # Trim the longer file to match durations
        input_audio = ffmpeg.input(audio_file).audio.filter('atrim', duration=video_duration)
        input_video = ffmpeg.input(video_file).video.filter('trim', duration=video_duration)

        # Concatenate audio and video streams
        output = ffmpeg.concat(input_video, input_audio, v=1, a=1).output('complete.mp4', y='-y')

        # Run ffmpeg command
        ffmpeg.run(output)
        print(f"Audio added to {video_file}. Output file: complete.mp4")
        # clean the files
        try:
            os.remove(audio_file)
            os.remove(video_file)
        except:
            print("Error occurred")

        return 'complete.mp4'
    
    except ffmpeg.Error as e:
        print(f"Error occurred: {e.stderr}")
        return None


def main(aud_url, vid_url, title, tags):
    audio_file = download_tiktok_audio(aud_url)
    video_file = get_video(vid_url)
    add_audio_to_video(audio_file, video_file)
    sleep(3)
    # upload video
    file = "complete.mp4"
    session_id = "ad496eea0112e18dbaf7710219abc7ea" # for @lucychacha900

    # Publish the video
    uploadVideo(session_id, file, title, tags, url_prefix="www")
    




aud_url = "https://www.tiktok.com/@maloneliness_/video/7321557757029551391"
vid_url = "https://www.tiktok.com/@.roshaun/video/7317972614541053215"

title = "spread love"
tags = ["fyp", "love", "now", "trending"]
main(aud_url, vid_url, title, tags)

