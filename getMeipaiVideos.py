#!/usr/bin/python -u
import base64
import json
import os
import re
import subprocess
import urllib2
import argparse
import wget
import pprint

from bs4 import BeautifulSoup


def strip_song_name(song_name):
    # Only chinese character
    song_chars = re.findall(ur'[\u4e00-\u9fff]+', song_name)
    output = " ".join(song_chars)
    # accomodate file system file name restriction
    return output[:100]
    

def get_user_song_map(user_id):
    user_load_url_template = "http://www.meipai.com/users/user_timeline?page={0}&count=10&single_column=1&uid={1}&maxid=476687454"

    song_map = {}

    for page_num in range(1, 100):
        url = user_load_url_template.format(page_num, user_id)
        content = urllib2.urlopen(url).read()
        songs = json.loads(content)[u'medias']

        if len(songs) == 0:
            break

        for song_obj in songs:
            song_name = song_obj[u'caption']
            song_name = strip_song_name(song_name)
            if (song_name == ""):
                continue
            song_url = song_obj[u'video'] 
            if song_url == "":
                print song_obj
            song_map[song_name] = song_url

    return song_map

def get_video_address(song_url):
    # Try cdn address first
    url = get_cdn_address(song_url)

    # If cdn address failed, try boke address
    if url == "":
        url = get_boke_video(song_url)

    return url

def download_video(video_name, video_url):
    if ".mp4" in video_url:
        video_name += ".mp4"
    elif ".flv" in video_url:
        video_name += ".flv"

    if os.path.isfile(video_name):
        # skip the video already downloaded
        print "Video already exists, skipping", video_name.encode('utf-8').strip()
        return

    print "Downloading", video_name.encode('utf-8').strip(), "from", video_url
    wget.download(video_url, video_name)
    print video_name.encode('utf-8').strip(), "download succeed."

def get_user_id_from_user_page(user_url):
    pattern = r"meipai.com/user/([0-9]+)"
    user_id_match = re.search(pattern, user_url)
    if user_id_match != None:
        return user_id_match.groups()[0]
    else:
        raise Exception("Can't find user id from user page")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Download video from changba.')
    parser.add_argument('--user-url', dest='user_url', type=str, required=True,
                                help='url of user page. Use this option will download all MV for that user')

    args = parser.parse_args()
    user_url = args.user_url

    user_id = get_user_id_from_user_page(user_url)

    song_map = get_user_song_map(user_id)

    for song_name, song_url in song_map.items():
        download_video(song_name, song_url)

    print "Done"        


