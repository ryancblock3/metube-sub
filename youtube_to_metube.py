#!/usr/bin/env python3
"""
YouTube to MeTube Automation Script

This script fetches the most recent n videos from a specified YouTube channel
and submits them to a MeTube instance for downloading.
"""

import requests
import json
import re
import sys
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import argparse
import time
from youtube_channel_scraper import YouTubeChannelScraper

class YouTubeToMeTube:
    def __init__(self, metube_url):
        self.metube_url = metube_url.rstrip('/')
        self.session = requests.Session()
        self.scraper = YouTubeChannelScraper()
        
    def get_channel_videos(self, channel_url, count=5, filter_content=True):
        """
        Get the most recent videos from a YouTube channel using the improved scraper.
        """
        return self.scraper.get_channel_videos(channel_url, count, filter_content)
    
    def submit_to_metube(self, video_url, quality='best', format_type='any'):
        """
        Submit a video URL to MeTube for downloading.
        """
        try:
            print(f"Submitting to MeTube: {video_url}")
            
            # MeTube API endpoint
            api_url = urljoin(self.metube_url, '/add')
            
            # Prepare data in the exact format MeTube expects
            data = {
                'url': video_url,
                'quality': quality,
                'format': format_type,
                'folder': '',
                'customNamePrefix': '',
                'playlistStrictMode': False,
                'playlistItemLimit': '',
                'autoStart': True
            }
            
            # Submit as JSON (MeTube expects JSON)
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            response = self.session.post(api_url, json=data, headers=headers)
            
            if response.status_code in [200, 201]:
                print(f"[SUCCESS] Successfully submitted: {video_url}")
                return True
            else:
                print(f"[FAILED] Failed to submit {video_url}: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"[ERROR] Error submitting {video_url}: {e}")
            return False
    
    def process_channel(self, channel_url, count=5, quality='best', format_type='any', filter_content=True):
        """
        Process a YouTube channel: fetch recent videos and submit them to MeTube.
        """
        print(f"Processing channel: {channel_url}")
        if filter_content:
            print(f"Fetching {count} most recent videos (filtering out member-only, Shorts, and livestreams)...")
        else:
            print(f"Fetching {count} most recent videos (no filtering)...")
        
        # Get recent videos from the channel
        video_urls = self.get_channel_videos(channel_url, count, filter_content)
        
        if not video_urls:
            print("No videos found or error occurred")
            return
        
        print(f"\nSubmitting {len(video_urls)} videos to MeTube...")
        
        successful = 0
        failed = 0
        
        for i, video_url in enumerate(video_urls, 1):
            print(f"\n[{i}/{len(video_urls)}] Processing: {video_url}")
            
            if self.submit_to_metube(video_url, quality, format_type):
                successful += 1
            else:
                failed += 1
            
            # Add a small delay between requests to be respectful
            if i < len(video_urls):
                time.sleep(1)
        
        print(f"\n=== Summary ===")
        print(f"Successfully submitted: {successful}")
        print(f"Failed: {failed}")
        print(f"Total processed: {len(video_urls)}")

def main():
    parser = argparse.ArgumentParser(description='Fetch recent YouTube videos and submit to MeTube')
    parser.add_argument('--metube-url', default='http://192.168.1.76:8081', 
                       help='MeTube instance URL (default: http://192.168.1.76:8081)')
    parser.add_argument('--channel', 
                       help='YouTube channel URL')
    parser.add_argument('--count', type=int, default=5, 
                       help='Number of recent videos to fetch (default: 5)')
    parser.add_argument('--quality', default='best', 
                       choices=['best', '2160p', '1440p', '1080p', '720p', '480p', 'worst', 'audio'],
                       help='Video quality (default: best)')
    parser.add_argument('--format', default='any', 
                       choices=['any', 'mp4', 'm4a', 'mp3', 'opus', 'wav', 'flac'],
                       help='Video format (default: any)')
    parser.add_argument('--test-video', 
                       help='Test with a specific video URL instead of fetching from channel')
    parser.add_argument('--no-filter', action='store_true',
                       help='Disable filtering (include member-only videos, Shorts, and livestreams)')
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.test_video and not args.channel:
        parser.error('Either --channel or --test-video must be specified')
    
    # Create the processor
    processor = YouTubeToMeTube(args.metube_url)
    
    if args.test_video:
        print(f"Testing with video: {args.test_video}")
        processor.submit_to_metube(args.test_video, args.quality, args.format)
    else:
        filter_content = not args.no_filter  # Default is to filter, unless --no-filter is specified
        processor.process_channel(args.channel, args.count, args.quality, args.format, filter_content)

if __name__ == '__main__':
    main()
