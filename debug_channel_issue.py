#!/usr/bin/env python3
"""Debug script to test channel ID extraction."""

import requests
import re

def test_channel_extraction(channel_url):
    print(f"Testing channel URL: {channel_url}")
    
    # Extract username
    if '/@' in channel_url:
        username = channel_url.split('/@')[-1].split('/')[0]
        print(f"Extracted username: {username}")
        
        # Test what happens when we fetch the page
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        test_url = f"https://www.youtube.com/@{username}"
        print(f"Fetching: {test_url}")
        
        try:
            response = session.get(test_url)
            print(f"Status code: {response.status_code}")
            
            if response.status_code == 200:
                # Look for channel ID patterns
                channel_id_pattern = r'"channelId":"([^"]+)"'
                matches = re.findall(channel_id_pattern, response.text)
                print(f"Found channelId patterns: {matches}")
                
                # Alternative pattern
                channel_id_pattern2 = r'<meta property="og:url" content="https://www\.youtube\.com/channel/([^"]+)"'
                matches2 = re.findall(channel_id_pattern2, response.text)
                print(f"Found meta og:url patterns: {matches2}")
                
                # Check if it's redirecting or showing wrong content
                if 'Daily Dose Of Internet' in response.text or 'DailyDoseOfInternet' in response.text:
                    print("Page contains Daily Dose Of Internet content")
                else:
                    print("Page does NOT contain Daily Dose Of Internet content")
                    
                # Look for actual channel name in page title
                title_pattern = r'<title>([^<]+)</title>'
                title_match = re.search(title_pattern, response.text)
                if title_match:
                    print(f"Page title: {title_match.group(1)}")
                
                # Test each channel ID to see which RSS feed is correct
                all_channel_ids = list(set(matches + matches2))
                print(f"\nTesting RSS feeds for all found channel IDs:")
                
                for channel_id in all_channel_ids:
                    rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
                    try:
                        rss_response = session.get(rss_url)
                        if rss_response.status_code == 200:
                            # Check if RSS contains Daily Dose content
                            if 'Daily Dose Of Internet' in rss_response.text:
                                print(f"CORRECT Channel ID {channel_id}: RSS contains Daily Dose Of Internet")
                            else:
                                print(f"WRONG Channel ID {channel_id}: RSS does NOT contain Daily Dose Of Internet")
                                # Show what channel it actually is
                                author_pattern = r'<name>([^<]+)</name>'
                                author_match = re.search(author_pattern, rss_response.text)
                                if author_match:
                                    print(f"  -> Actually contains: {author_match.group(1)}")
                        else:
                            print(f"? Channel ID {channel_id}: RSS fetch failed ({rss_response.status_code})")
                    except Exception as e:
                        print(f"? Channel ID {channel_id}: RSS fetch error - {e}")
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_channel_extraction("https://www.youtube.com/@DailyDoseOfInternet")