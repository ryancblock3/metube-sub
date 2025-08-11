#!/usr/bin/env python3
"""
Example usage of the YouTube to MeTube automation tool.

This script demonstrates different ways to use the tool.
"""

import subprocess
import sys

def run_command(cmd):
    """Run a command and print the output."""
    print(f"\n{'='*60}")
    print(f"Running: {cmd}")
    print('='*60)
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running command: {e}")
        return False

def main():
    print("YouTube to MeTube Automation Tool - Example Usage")
    print("=" * 60)
    
    # Example 1: Test with the provided video
    print("\n1. Testing with a single video:")
    test_video_cmd = 'python youtube_to_metube.py --test-video "https://www.youtube.com/watch?v=gXVpAVwN8F0"'
    run_command(test_video_cmd)
    
    # Example 2: Show help
    print("\n2. Showing help information:")
    help_cmd = 'python youtube_to_metube.py --help'
    run_command(help_cmd)
    
    # Example 3: Example channel command (commented out to avoid actual execution)
    print("\n3. Example channel commands (not executed):")
    print("   # Fetch 3 videos from a tech channel:")
    print('   python youtube_to_metube.py --channel "https://www.youtube.com/@TechChannel" --count 3')
    print("\n   # Fetch 5 videos in 720p:")
    print('   python youtube_to_metube.py --channel "https://www.youtube.com/@SomeChannel" --quality 720p')
    print("\n   # Fetch audio only:")
    print('   python youtube_to_metube.py --channel "https://www.youtube.com/@MusicChannel" --quality audio --format mp3')

if __name__ == '__main__':
    main()
