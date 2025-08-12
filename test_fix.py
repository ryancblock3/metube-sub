#!/usr/bin/env python3
"""Test the fixed channel scraper."""

from youtube_channel_scraper import YouTubeChannelScraper

def test_fixed_scraper():
    scraper = YouTubeChannelScraper()
    
    print("Testing Daily Dose Of Internet...")
    videos = scraper.get_channel_videos("https://www.youtube.com/@DailyDoseOfInternet", count=3, filter_content=False)
    
    print(f"\nFound {len(videos)} videos:")
    for i, video in enumerate(videos, 1):
        print(f"{i}. {video}")
    
    return videos

if __name__ == "__main__":
    test_fixed_scraper()