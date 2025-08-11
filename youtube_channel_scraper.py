#!/usr/bin/env python3
"""
Enhanced YouTube Channel Scraper

This module provides better methods for extracting video URLs from YouTube channels.
"""

import requests
import json
import re
from urllib.parse import urljoin
import time
from bs4 import BeautifulSoup

class YouTubeChannelScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def get_channel_videos_rss(self, channel_url, count=5):
        """
        Get recent videos using YouTube RSS feed (more reliable).
        """
        try:
            # Extract channel ID from various URL formats
            channel_id = self._extract_channel_id(channel_url)
            if not channel_id:
                print(f"Could not extract channel ID from: {channel_url}")
                return []
            
            # Use YouTube RSS feed
            rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
            print(f"Fetching RSS feed: {rss_url}")
            
            response = self.session.get(rss_url)
            response.raise_for_status()
            
            # Parse RSS XML to extract video IDs
            video_urls = []
            
            # Simple regex to find video IDs in RSS feed
            video_id_pattern = r'<yt:videoId>([^<]+)</yt:videoId>'
            video_ids = re.findall(video_id_pattern, response.text)
            
            # Convert to full URLs and limit to requested count
            for video_id in video_ids[:count]:
                video_urls.append(f"https://www.youtube.com/watch?v={video_id}")
            
            print(f"Found {len(video_urls)} videos from RSS feed")
            return video_urls
            
        except Exception as e:
            print(f"Error fetching RSS feed: {e}")
            return []
    
    def _extract_channel_id(self, channel_url):
        """
        Extract channel ID from various YouTube URL formats.
        """
        try:
            # Direct channel ID
            if '/channel/' in channel_url:
                return channel_url.split('/channel/')[-1].split('/')[0]
            
            # Handle @username format
            if '/@' in channel_url:
                username = channel_url.split('/@')[-1].split('/')[0]
                return self._get_channel_id_from_username(username)
            
            # Handle /c/ format
            if '/c/' in channel_url:
                username = channel_url.split('/c/')[-1].split('/')[0]
                return self._get_channel_id_from_username(username)
            
            # Handle /user/ format
            if '/user/' in channel_url:
                username = channel_url.split('/user/')[-1].split('/')[0]
                return self._get_channel_id_from_username(username)
            
            return None
            
        except Exception as e:
            print(f"Error extracting channel ID: {e}")
            return None
    
    def _get_channel_id_from_username(self, username):
        """
        Get channel ID from username by scraping the channel page.
        """
        try:
            # Try different URL formats
            possible_urls = [
                f"https://www.youtube.com/@{username}",
                f"https://www.youtube.com/c/{username}",
                f"https://www.youtube.com/user/{username}"
            ]
            
            for url in possible_urls:
                try:
                    response = self.session.get(url)
                    if response.status_code == 200:
                        # Look for channel ID in the page
                        channel_id_pattern = r'"channelId":"([^"]+)"'
                        match = re.search(channel_id_pattern, response.text)
                        if match:
                            return match.group(1)
                        
                        # Alternative pattern
                        channel_id_pattern2 = r'<meta property="og:url" content="https://www\.youtube\.com/channel/([^"]+)"'
                        match2 = re.search(channel_id_pattern2, response.text)
                        if match2:
                            return match2.group(1)
                            
                except Exception:
                    continue
            
            return None
            
        except Exception as e:
            print(f"Error getting channel ID from username: {e}")
            return None
    
    def get_channel_videos_scrape(self, channel_url, count=5):
        """
        Fallback method: scrape the channel page directly.
        """
        try:
            print(f"Scraping channel page: {channel_url}")
            
            # Ensure we have a proper channel URL
            if not channel_url.endswith('/videos'):
                if channel_url.endswith('/'):
                    channel_url = channel_url + 'videos'
                else:
                    channel_url = channel_url + '/videos'
            
            response = self.session.get(channel_url)
            response.raise_for_status()
            
            # Extract video IDs from the page
            video_urls = []
            
            # Multiple patterns to catch different page structures
            patterns = [
                r'"videoId":"([^"]+)"',
                r'/watch\?v=([a-zA-Z0-9_-]{11})',
                r'watch\?v=([a-zA-Z0-9_-]{11})'
            ]
            
            all_video_ids = set()
            
            for pattern in patterns:
                video_ids = re.findall(pattern, response.text)
                all_video_ids.update(video_ids)
            
            # Convert to list and limit
            video_ids_list = list(all_video_ids)[:count]
            
            for video_id in video_ids_list:
                if len(video_id) == 11:  # YouTube video IDs are 11 characters
                    video_urls.append(f"https://www.youtube.com/watch?v={video_id}")
            
            print(f"Found {len(video_urls)} videos from scraping")
            return video_urls
            
        except Exception as e:
            print(f"Error scraping channel page: {e}")
            return []
    
    def _is_video_valid(self, video_url):
        """
        Check if a video is valid (not member-only, not a Short, not a livestream).
        """
        try:
            response = self.session.get(video_url)
            response.raise_for_status()
            
            # Check for member-only content
            if 'Join this channel to get access to perks' in response.text or \
               'members-only' in response.text.lower() or \
               '"isLiveContent":true' in response.text:
                return False, "member-only or live content"
            
            # Check for YouTube Shorts (multiple indicators)
            if '"isShort":true' in response.text or \
               '/shorts/' in response.text or \
               '"shortFormVideoDetails"' in response.text:
                return False, "YouTube Short"
            
            # Check for livestreams
            if '"isLiveContent":true' in response.text or \
               '"liveBroadcastContent":"live"' in response.text or \
               '"liveBroadcastContent":"upcoming"' in response.text:
                return False, "livestream"
            
            # Additional check for very short videos (likely Shorts)
            duration_match = re.search(r'"lengthSeconds":"(\d+)"', response.text)
            if duration_match:
                duration = int(duration_match.group(1))
                if duration <= 60:  # Videos 60 seconds or less are likely Shorts
                    return False, "short video (≤60s)"
            
            return True, "valid"
            
        except Exception as e:
            print(f"Error checking video {video_url}: {e}")
            return True, "unknown (assuming valid)"  # If we can't check, assume it's valid
    
    def _filter_videos(self, video_urls, target_count):
        """
        Filter out member-only videos, Shorts, and livestreams.
        """
        print(f"Filtering videos to exclude member-only, Shorts, and livestreams...")
        
        valid_videos = []
        checked_count = 0
        
        for video_url in video_urls:
            if len(valid_videos) >= target_count:
                break
                
            checked_count += 1
            print(f"Checking video {checked_count}: {video_url}")
            
            is_valid, reason = self._is_video_valid(video_url)
            
            if is_valid:
                valid_videos.append(video_url)
                print(f"  ✓ Valid video added ({len(valid_videos)}/{target_count})")
            else:
                print(f"  ✗ Skipped: {reason}")
            
            # Add a small delay to be respectful
            time.sleep(0.5)
        
        print(f"Filtered {len(valid_videos)} valid videos from {checked_count} checked")
        return valid_videos
    
    def get_channel_videos(self, channel_url, count=5, filter_content=True):
        """
        Get recent videos from a channel using multiple methods.
        """
        print(f"Fetching {count} recent videos from: {channel_url}")
        
        # Fetch more videos initially to account for filtering
        fetch_count = count * 3 if filter_content else count
        
        # Try RSS feed first (most reliable)
        videos = self.get_channel_videos_rss(channel_url, fetch_count)
        
        if not videos:
            print("RSS method failed, trying direct scraping...")
            # Fallback to scraping
            videos = self.get_channel_videos_scrape(channel_url, fetch_count)
        
        if not videos:
            return []
        
        # Filter videos if requested
        if filter_content:
            videos = self._filter_videos(videos, count)
        else:
            videos = videos[:count]
        
        return videos
