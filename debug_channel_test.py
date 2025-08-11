#!/usr/bin/env python3
"""
Debug script to test channel video fetching without submitting to MeTube.
"""

import sys
from youtube_channel_scraper import YouTubeChannelScraper

def test_channel_scraping(channel_url, count=10):
    """Test channel scraping and show detailed results."""
    print(f"Testing channel scraping for: {channel_url}")
    print("=" * 60)
    
    scraper = YouTubeChannelScraper()
    
    # Test RSS method
    print("\n1. Testing RSS feed method:")
    print("-" * 30)
    rss_videos = scraper.get_channel_videos_rss(channel_url, count * 2)  # Get more for filtering test
    if rss_videos:
        print(f"RSS method found {len(rss_videos)} videos:")
        for i, video in enumerate(rss_videos, 1):
            print(f"  {i}. {video}")
    else:
        print("RSS method failed or found no videos")
    
    # Test scraping method
    print("\n2. Testing web scraping method:")
    print("-" * 30)
    scrape_videos = scraper.get_channel_videos_scrape(channel_url, count)
    if scrape_videos:
        print(f"Scraping method found {len(scrape_videos)} videos:")
        for i, video in enumerate(scrape_videos, 1):
            print(f"  {i}. {video}")
    else:
        print("Scraping method failed or found no videos")
    
    # Test combined method without filtering
    print("\n3. Testing combined method without filtering:")
    print("-" * 30)
    unfiltered_videos = scraper.get_channel_videos(channel_url, count, filter_content=False)
    if unfiltered_videos:
        print(f"Unfiltered method found {len(unfiltered_videos)} videos:")
        for i, video in enumerate(unfiltered_videos, 1):
            print(f"  {i}. {video}")
    else:
        print("Unfiltered method failed or found no videos")
    
    # Test combined method with filtering
    print("\n4. Testing combined method WITH filtering (member-only, Shorts, livestreams):")
    print("-" * 30)
    filtered_videos = scraper.get_channel_videos(channel_url, count, filter_content=True)
    if filtered_videos:
        print(f"Filtered method found {len(filtered_videos)} videos:")
        for i, video in enumerate(filtered_videos, 1):
            print(f"  {i}. {video}")
    else:
        print("Filtered method failed or found no videos")
    
    return filtered_videos

def main():
    if len(sys.argv) < 2:
        print("Usage: python debug_channel_test.py <channel_url> [count]")
        print("Example: python debug_channel_test.py 'https://www.youtube.com/@channelname' 5")
        return
    
    channel_url = sys.argv[1]
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    
    test_channel_scraping(channel_url, count)

if __name__ == '__main__':
    main()
