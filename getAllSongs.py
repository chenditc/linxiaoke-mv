#!/Users/chensusumu/anaconda/bin/python
import base64
import json
import os
import re
import subprocess
import urllib2
import argparse
import wget


from bs4 import BeautifulSoup

def get_user_song_map(user_id):
    user_load_url_template = "http://changba.com/member/personcenter/loadmore.php?pageNum={0}&userid={1}"

    song_map = {}

    for page_num in range(0, 100):
        url = user_load_url_template.format(page_num, user_id)
        content = urllib2.urlopen(url).read()
        songs = json.loads(content)

        if len(songs) == 0:
            break

        for song_obj in songs:
            song_name = song_obj["songname"]
            song_url = "http://changba.com/s/{0}".format(song_obj["enworkid"])
            song_map[song_name] = song_url

    return song_map

def get_boke_video(song_url):
    # get html content
    html = urllib2.urlopen(song_url).read()
    match = re.search(r"vid=([0-9A-Z]+)&", html)
    if match == None:
        return ""
    
    vid = match.groups()[0]

    # request real address
    info_request_template = "http://p.bokecc.com/servlet/playinfo?uid=2745FC107AA7B1F3&vid={0}&m=0"
    info_request_url = info_request_template.format(vid)

    info_response = urllib2.urlopen(info_request_url).read()
    soup = BeautifulSoup(info_response, 'xml')

    video_qualities = soup.find_all("quality")
    for video_quality in video_qualities:
        if video_quality.get("desp") == u'\u6e05\u6670': # qing xi
            video_copy = video_quality.find_all("copy")[0]
            video_url = video_copy.get("playurl")
            return video_url

    return "" 

def get_cdn_address(song_url):
    # get html content
    html = urllib2.urlopen(song_url).read()
    soup = BeautifulSoup(html, 'html.parser')

    # get qn string
    lines = soup.find_all('script') 
    lines = [ line.get_text() for line in lines ] 
    qn = ""
    for line in lines: 
        qn_match = re.search(r'jwplayer.utils.qn.*\'(.*)\'', html)
        if qn_match != None:
            qn = qn_match.groups()[0]

    video_url = base64.b64decode(qn)

    return video_url


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
        print "Video already exists, skipping", video_name
        return

    print "Downloading", video_name, "from", video_url
    wget.download(video_url, video_name)
    print video_name, "download succeed."
    quit()

def get_user_id_from_user_page(user_url):
    html = urllib2.urlopen(user_url).read()
    soup = BeautifulSoup(html, 'html.parser')
    scripts = soup.find_all("script")
    lines = [ dom.get_text() for dom in scripts ]

    user_id_match = re.search(r'userid.*\'(\d+)\'', html)
    if user_id_match != None:
        return user_id_match.groups()[0]
    else:
        raise Exception("Can't find user id from user page")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Download video from changba.')
    parser.add_argument('--user-url', dest='user_url', type=str,
                                help='url of user page. Use this option will download all MV for that user')
    parser.add_argument('--song-url', dest='song_url', type=str,
                                help='Url of the MV page, which you can stream online ')

    args = parser.parse_args()
    user_url = args.user_url
    song_url = args.song_url

    if user_url != None:
        user_id = get_user_id_from_user_page(user_url)

        song_map = get_user_song_map(user_id)
        video_map = {}
        for song_name, song_url in song_map.items():
            video_url = get_video_address(song_url)
            if video_url != "":
                video_map[song_name] = video_url
                download_video(song_name, video_url)


    print "Done"        


