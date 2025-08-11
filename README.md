# YouTube to MeTube Automation Tool

This tool automatically fetches the most recent videos from a specified YouTube channel and submits them to a MeTube instance for downloading.

## Features

- Fetch recent videos from YouTube channels using multiple methods (RSS feed and web scraping)
- **Smart filtering** to automatically exclude member-only videos, YouTube Shorts, and livestreams
- Submit videos to MeTube for automatic downloading
- Support for various video qualities and formats
- Configurable number of videos to fetch
- Test mode for single video submissions

## Requirements

- Python 3.6+
- MeTube instance running and accessible

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

Fetch the 5 most recent videos from a channel and submit to MeTube:
```bash
python youtube_to_metube.py --channel "https://www.youtube.com/@channelname"
```

### Advanced Usage

Fetch 10 videos in 1080p MP4 format:
```bash
python youtube_to_metube.py --channel "https://www.youtube.com/@channelname" --count 10 --quality 1080p --format mp4
```

Use a custom MeTube instance:
```bash
python youtube_to_metube.py --channel "https://www.youtube.com/@channelname" --metube-url "http://your-metube-server:8081"
```

### Test Mode

Test with a single video:
```bash
python youtube_to_metube.py --test-video "https://www.youtube.com/watch?v=VIDEO_ID"
```

## Supported Channel URL Formats

- `https://www.youtube.com/@username`
- `https://www.youtube.com/channel/CHANNEL_ID`
- `https://www.youtube.com/c/channelname`
- `https://www.youtube.com/user/username`

## Command Line Options

- `--metube-url`: MeTube instance URL (default: http://192.168.1.76:8081)
- `--channel`: YouTube channel URL
- `--count`: Number of recent videos to fetch (default: 5)
- `--quality`: Video quality (best, 2160p, 1440p, 1080p, 720p, 480p, worst, audio)
- `--format`: Video format (any, mp4, m4a, mp3, opus, wav, flac)
- `--test-video`: Test with a specific video URL
- `--no-filter`: Disable filtering (include member-only videos, Shorts, and livestreams)

## How It Works

1. **Channel Discovery**: The tool extracts the channel ID from various YouTube URL formats
2. **Video Fetching**: Uses YouTube RSS feeds (primary method) or web scraping (fallback) to get recent videos
3. **MeTube Submission**: Submits each video URL to the MeTube API for downloading
4. **Progress Tracking**: Shows real-time progress and summary of successful/failed submissions

## Examples

### Example 1: Technology Channel
```bash
python youtube_to_metube.py --channel "https://www.youtube.com/@TechChannel" --count 3 --quality 720p
```

### Example 2: Music Channel (Audio Only)
```bash
python youtube_to_metube.py --channel "https://www.youtube.com/@MusicChannel" --count 10 --quality audio --format mp3
```

### Example 3: Test Single Video
```bash
python youtube_to_metube.py --test-video "https://www.youtube.com/watch?v=gXVpAVwN8F0"
```

### Example 4: Disable Filtering (Include All Content)
```bash
python youtube_to_metube.py --channel "https://www.youtube.com/@channelname" --count 5 --no-filter
```

### Example 5: Channel with Filtering (Default Behavior)
```bash
python youtube_to_metube.py --channel "https://www.youtube.com/@channelname" --count 10 --quality best
```
*This will automatically skip member-only videos, YouTube Shorts, and livestreams*

## Troubleshooting

### Common Issues

1. **No videos found**: 
   - Check if the channel URL is correct
   - Some channels may have restricted access to their video lists

2. **MeTube connection failed**:
   - Verify the MeTube instance is running
   - Check the MeTube URL is correct
   - Ensure network connectivity

3. **Videos not downloading**:
   - Check MeTube logs for download errors
   - Some videos may be geo-restricted or have other limitations

### Debug Mode

For more detailed output, you can modify the script to add debug logging or run with verbose output.

## Notes

- The tool respects rate limits by adding delays between requests
- RSS feed method is more reliable but may not work for all channels
- Web scraping is used as a fallback but may be less reliable due to YouTube's dynamic content
- For production use, consider using the official YouTube Data API for better reliability

## License

This tool is provided as-is for educational and personal use.
