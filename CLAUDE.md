# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

### Installation
```bash
pip install -r requirements.txt
```

### Running the Tool

**Web GUI (recommended):**
```bash
python web_gui.py
# Open http://localhost:5000 in your browser
```

**Command Line:**
```bash
# Test with a single video
python youtube_to_metube.py --test-video "https://www.youtube.com/watch?v=VIDEO_ID"

# Fetch recent videos from a channel
python youtube_to_metube.py --channel "https://www.youtube.com/@channelname"

# Fetch with specific options
python youtube_to_metube.py --channel "https://www.youtube.com/@channelname" --count 10 --quality 1080p --format mp4
```

**Desktop GUI:**
```bash
python youtube_metube_gui.py
```

**Debug and Testing:**
```bash
# Debug channel scraping without MeTube submission
python debug_channel_test.py "https://www.youtube.com/@channelname" 5

# Verify video titles and check what's being found
python verify_videos.py

# Example usage demonstrations
python example_usage.py
```

## Code Architecture

### Core Components

**youtube_to_metube.py** - Main automation script
- `YouTubeToMeTube` class: Orchestrates the entire process from YouTube to MeTube
- Handles MeTube API submission via POST to `/add` endpoint
- Manages command-line interface and argument parsing

**youtube_channel_scraper.py** - YouTube video discovery engine
- `YouTubeChannelScraper` class: Multi-method video fetching strategy
- Primary method: RSS feed parsing (`/feeds/videos.xml?channel_id=X`)
- Fallback method: Direct web scraping of channel pages
- Smart filtering system to exclude member-only videos, YouTube Shorts (≤60s), and livestreams
- Channel ID extraction supporting multiple URL formats (`/@username`, `/channel/ID`, `/c/name`, `/user/name`)

### Data Flow

1. **Channel Resolution**: URL → Channel ID extraction
2. **Video Discovery**: RSS feed (preferred) → Web scraping (fallback)  
3. **Content Filtering**: Validates videos to exclude restricted/short content
4. **MeTube Integration**: REST API submission with quality/format options

### Key Configuration

- Default MeTube URL: `http://192.168.1.76:8081`
- Supported qualities: best, 2160p, 1440p, 1080p, 720p, 480p, worst, audio
- Supported formats: any, mp4, m4a, mp3, opus, wav, flac
- Rate limiting: 1-second delays between MeTube submissions, 0.5s for video validation

### Dependencies

- `requests`: HTTP client for API calls and web scraping
- `beautifulsoup4 + lxml`: HTML parsing for channel scraping
- Standard library: `json`, `re`, `argparse`, `time`, `urllib.parse`