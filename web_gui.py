#!/usr/bin/env python3
"""
YouTube to MeTube Web GUI

A modern web interface for the YouTube to MeTube automation tool.
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_socketio import SocketIO, emit
import threading
import time
import json
import re
import requests
from youtube_to_metube import YouTubeToMeTube
from youtube_channel_scraper import YouTubeChannelScraper

app = Flask(__name__)
app.config['SECRET_KEY'] = 'youtube-metube-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

class WebGUIHandler:
    def __init__(self):
        self.is_running = False
        self.current_videos = []
        self.video_details = {}
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def emit_log(self, message, level="info"):
        """Emit log message to connected clients."""
        socketio.emit('log_message', {'message': message, 'level': level})
        print(f"[{level.upper()}] {message}")
    
    def fetch_videos(self, channel_url, count, filter_content):
        """Fetch videos from YouTube channel."""
        try:
            self.emit_log(f"Fetching {count} videos from: {channel_url}")
            if filter_content:
                self.emit_log("Filtering enabled: excluding member-only, Shorts, and livestreams")
            
            scraper = YouTubeChannelScraper()
            videos = scraper.get_channel_videos(channel_url, count, filter_content)
            
            if videos:
                self.current_videos = videos
                self.emit_log(f"Successfully found {len(videos)} videos")
                
                # Get video details for better quality control
                video_details = self._get_video_details(videos)
                self.video_details = video_details
                
                socketio.emit('videos_found', {'videos': videos, 'details': video_details})
                return videos
            else:
                self.emit_log("No videos found", "warning")
                return []
                
        except Exception as e:
            self.emit_log(f"Error fetching videos: {e}", "error")
            return []
    
    def submit_videos(self, videos, metube_url, quality, format_type):
        """Submit videos to MeTube."""
        try:
            processor = YouTubeToMeTube(metube_url)
            
            self.emit_log(f"Submitting {len(videos)} videos to MeTube...")
            self.emit_log(f"Quality: {quality}, Format: {format_type}")
            
            successful = 0
            failed = 0
            
            for i, video_url in enumerate(videos, 1):
                self.emit_log(f"[{i}/{len(videos)}] Processing: {video_url}")
                socketio.emit('progress_update', {
                    'current': i, 
                    'total': len(videos), 
                    'video_url': video_url
                })
                
                if processor.submit_to_metube(video_url, quality, format_type):
                    successful += 1
                    self.emit_log(f"✓ Successfully submitted")
                    socketio.emit('video_result', {'video_url': video_url, 'success': True})
                else:
                    failed += 1
                    self.emit_log(f"✗ Failed to submit", "error")
                    socketio.emit('video_result', {'video_url': video_url, 'success': False})
                
                if i < len(videos):
                    time.sleep(1)
            
            self.emit_log(f"\n=== Summary ===")
            self.emit_log(f"Successfully submitted: {successful}")
            self.emit_log(f"Failed: {failed}")
            self.emit_log(f"Total processed: {len(videos)}")
            
            socketio.emit('submission_complete', {
                'successful': successful,
                'failed': failed,
                'total': len(videos)
            })
            
        except Exception as e:
            self.emit_log(f"Error during submission: {e}", "error")
    
    def submit_videos_with_quality(self, selected_videos, metube_url, format_type):
        """Submit videos with individual quality settings."""
        try:
            processor = YouTubeToMeTube(metube_url)
            
            self.emit_log(f"Submitting {len(selected_videos)} videos to MeTube...")
            self.emit_log(f"Format: {format_type}")
            
            successful = 0
            failed = 0
            
            for i, video_data in enumerate(selected_videos, 1):
                video_url = video_data['url']
                quality = video_data['quality']
                
                self.emit_log(f"[{i}/{len(selected_videos)}] Processing: {video_url} (Quality: {quality})")
                socketio.emit('progress_update', {
                    'current': i, 
                    'total': len(selected_videos), 
                    'video_url': video_url
                })
                
                if processor.submit_to_metube(video_url, quality, format_type):
                    successful += 1
                    self.emit_log(f"✓ Successfully submitted")
                    socketio.emit('video_result', {'video_url': video_url, 'success': True})
                else:
                    failed += 1
                    self.emit_log(f"✗ Failed to submit", "error")
                    socketio.emit('video_result', {'video_url': video_url, 'success': False})
                
                if i < len(selected_videos):
                    time.sleep(1)
            
            self.emit_log(f"\n=== Summary ===")
            self.emit_log(f"Successfully submitted: {successful}")
            self.emit_log(f"Failed: {failed}")
            self.emit_log(f"Total processed: {len(selected_videos)}")
            
            socketio.emit('submission_complete', {
                'successful': successful,
                'failed': failed,
                'total': len(selected_videos)
            })
            
        except Exception as e:
            self.emit_log(f"Error during submission: {e}", "error")
    
    def _get_video_details(self, videos):
        """Get basic details for videos including titles and durations."""
        details = {}
        
        for video_url in videos:
            try:
                self.emit_log(f"Getting details for: {video_url}")
                response = self.session.get(video_url)
                
                if response.status_code == 200:
                    # Extract title
                    title_match = re.search(r'"title":"([^"]*)"', response.text)
                    title = title_match.group(1) if title_match else "Unknown Title"
                    
                    # Extract duration
                    duration_match = re.search(r'"lengthSeconds":"(\d+)"', response.text)
                    duration_seconds = int(duration_match.group(1)) if duration_match else 0
                    
                    # Extract video ID for thumbnail
                    video_id_match = re.search(r'watch\?v=([a-zA-Z0-9_-]{11})', video_url)
                    video_id = video_id_match.group(1) if video_id_match else ""
                    
                    # YouTube thumbnail URLs (high quality first, then fallbacks)
                    thumbnail_urls = [
                        f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
                        f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
                        f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg"
                    ]
                    
                    # Convert to readable format
                    hours = duration_seconds // 3600
                    minutes = (duration_seconds % 3600) // 60
                    seconds = duration_seconds % 60
                    
                    if hours > 0:
                        duration_str = f"{hours}:{minutes:02d}:{seconds:02d}"
                    else:
                        duration_str = f"{minutes}:{seconds:02d}"
                    
                    details[video_url] = {
                        'title': title.encode('utf-8').decode('unicode_escape'),
                        'duration': duration_str,
                        'duration_seconds': duration_seconds,
                        'video_id': video_id,
                        'thumbnail_urls': thumbnail_urls
                    }
                    
                    # Suggest quality based on duration
                    if duration_seconds > 3600:  # > 1 hour
                        suggested_quality = "720p"  # Lower quality for long videos
                    elif duration_seconds > 1800:  # > 30 min
                        suggested_quality = "1080p"
                    else:
                        suggested_quality = "best"
                    
                    details[video_url]['suggested_quality'] = suggested_quality
                
            except Exception as e:
                video_id_match = re.search(r'watch\?v=([a-zA-Z0-9_-]{11})', video_url)
                video_id = video_id_match.group(1) if video_id_match else ""
                
                details[video_url] = {
                    'title': 'Error loading title',
                    'duration': 'Unknown',
                    'duration_seconds': 0,
                    'suggested_quality': 'best',
                    'video_id': video_id,
                    'thumbnail_urls': [
                        f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
                        f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg"
                    ] if video_id else []
                }
                
        return details

handler = WebGUIHandler()

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('fetch_videos')
def handle_fetch_videos(data):
    if handler.is_running:
        emit('error', {'message': 'Operation already in progress'})
        return
    
    handler.is_running = True
    emit('operation_started')
    
    def fetch_thread():
        try:
            videos = handler.fetch_videos(
                data['channel_url'],
                int(data['count']),
                data['filter_content']
            )
        finally:
            handler.is_running = False
            socketio.emit('operation_finished')
    
    thread = threading.Thread(target=fetch_thread)
    thread.daemon = True
    thread.start()

@socketio.on('submit_videos')
def handle_submit_videos(data):
    if handler.is_running:
        emit('error', {'message': 'Operation already in progress'})
        return
    
    if not handler.current_videos:
        emit('error', {'message': 'No videos to submit. Fetch videos first.'})
        return
    
    handler.is_running = True
    emit('operation_started')
    
    def submit_thread():
        try:
            selected_videos = data.get('selected_videos', [])
            
            handler.submit_videos_with_quality(
                selected_videos,
                data['metube_url'],
                data['format_type']
            )
        finally:
            handler.is_running = False
            socketio.emit('operation_finished')
    
    thread = threading.Thread(target=submit_thread)
    thread.daemon = True
    thread.start()

@socketio.on('test_video')
def handle_test_video(data):
    if handler.is_running:
        emit('error', {'message': 'Operation already in progress'})
        return
    
    handler.is_running = True
    emit('operation_started')
    
    def test_thread():
        try:
            handler.submit_videos(
                [data['video_url']],
                data['metube_url'],
                data['quality'],
                data['format_type']
            )
        finally:
            handler.is_running = False
            socketio.emit('operation_finished')
    
    thread = threading.Thread(target=test_thread)
    thread.daemon = True
    thread.start()

@socketio.on('connect')
def handle_connect():
    emit('connected', {'data': 'Connected to YouTube to MeTube server'})

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)