from flask import Flask, Response
import feedparser
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import os
import json
import requests

app = Flask(__name__)

# The URL of the original FitGirl Repacks RSS feed
rss_url = 'https://fitgirl-repacks.site/feed/'

# Paths for cache files
cache_path = 'feed_cache.xml'

def fetch_and_cache_feed():
    feed = feedparser.parse(rss_url)
    with open(cache_path, 'w') as file:
        json.dump(feed, file)
    return feed

def load_cached_feed():
    if os.path.exists(cache_path):
        with open(cache_path) as file:
            return json.load(file)
    else:
        return None

def generate_rss_feed(feed):
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = "Custom RSS feed for FitGirl Repacks"
    ET.SubElement(channel, "link").text = "http://localhost:5000/"
    ET.SubElement(channel, "description").text = "Custom RSS feed for FitGirl Repacks"
    list = []

    for entry in feed['entries']:
        for tag in entry.get('tags',[]):
            if "Lossless Repack" == tag['term']:
                content = entry.get('content', [{}])[0].get('value', entry.get('summary', ''))
                soup = BeautifulSoup(content, 'html.parser')
                item = ET.SubElement(channel, "item")
                magnet_tag = soup.find('a', href=lambda href: href and href.startswith('magnet:'))
                ET.SubElement(item, "title").text = entry.get('title')
                try:
                    ET.SubElement(item, "link").text = magnet_tag['href']
                except:
                    try:
                        if magnet_tag == None:
                            forumlink = soup.find('a', href=lambda href: href and href.startswith('https://cs.rin.ru'))
                            response = requests.get(forumlink['href'] + "&start=9999").text
                            soup = BeautifulSoup(response, 'html.parser')
                            for line in soup.get_text('\n', strip=True).split("\n"):
                                if line.startswith('magnet:'):
                                   ET.SubElement(item, "link").text = line
                    except:
                        ET.SubElement(item, "link").text = entry.get('link')
                ET.SubElement(item, "description").text = entry.get('description')
                ET.SubElement(item, "pubDate").text = entry.get('published')
                
    return ET.tostring(rss, encoding='unicode')

@app.route("/")
def rss_feed():
    try:
        feed = fetch_and_cache_feed()
    except Exception as e:
        feed = load_cached_feed()
        if feed is None:
            return "Error fetching feed and no cache available.", 500

    rss_feed_content = generate_rss_feed(feed)
    return Response(rss_feed_content, mimetype='application/rss+xml')

if __name__ == "__main__":
    app.run(debug=True)
