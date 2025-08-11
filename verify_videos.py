#!/usr/bin/env python3
"""
Verify what videos are being found by checking their titles.
"""

import requests
from bs4 import BeautifulSoup
import re

def get_video_title(video_url):
    """Get the title of a YouTube video."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(video_url, headers=headers)
        response.raise_for_status()
        
        # Look for the title in the page
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try multiple methods to find the title
        title = None
        
        # Method 1: meta property
        meta_title = soup.find('meta', property='og:title')
        if meta_title:
            title = meta_title.get('content')
        
        # Method 2: title tag
        if not title:
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.text.replace(' - YouTube', '')
        
        # Method 3: JSON-LD
        if not title:
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                try:
                    import json
                    data = json.loads(script.string)
                    if isinstance(data, list):
                        data = data[0]
                    if 'name' in data:
                        title = data['name']
                        break
                except:
                    continue
        
        return title or "Title not found"
        
    except Exception as e:
        return f"Error: {e}"

def main():
    # Test the videos found by RSS feed
    rss_videos = [
        "https://www.youtube.com/watch?v=4-g03myoFRE",
        "https://www.youtube.com/watch?v=c9ttpokDl-I", 
        "https://www.youtube.com/watch?v=vh3IvaZqdp4",
        "https://www.youtube.com/watch?v=Xrq5qRNAHRM",
        "https://www.youtube.com/watch?v=8VVtnfp03zQ"
    ]
    
    print("RSS Feed Videos (what the tool is currently finding):")
    print("=" * 60)
    for i, video_url in enumerate(rss_videos, 1):
        title = get_video_title(video_url)
        print(f"{i}. {title}")
        print(f"   URL: {video_url}")
        print()

if __name__ == '__main__':
    main()
