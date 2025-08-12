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
    
    def get_downloaded_videos(self, metube_url):
        """Get list of currently available downloaded videos from MeTube."""
        try:
            self.emit_log("Fetching current downloads from MeTube...")
            
            # Try to get current status instead of history
            status_url = f"{metube_url.rstrip('/')}/downloads"
            response = self.session.get(status_url)
            
            if response.status_code == 200:
                # Use current downloads endpoint if available
                downloads_data = response.json()
                downloaded_videos = []
                
                # Check if there's a 'done' section in current downloads
                if isinstance(downloads_data, dict) and 'done' in downloads_data:
                    for video in downloads_data['done']:
                        # Handle missing filesize - try to estimate or mark as unknown
                        filesize = video.get('filesize')
                        if filesize is None:
                            # MeTube sometimes doesn't have filesize, try to estimate or mark clearly
                            filesize = 'unknown'
                        
                        video_info = {
                            'id': video.get('id'),
                            'title': video.get('title', 'Unknown Title'),
                            'url': video.get('url'),
                            'filename': video.get('filename'),
                            'timestamp': video.get('timestamp'),
                            'filesize': filesize,
                            'status': video.get('status'),
                            'folder': video.get('folder', ''),
                            'filepath': video.get('filepath', video.get('filename', ''))
                        }
                        self.emit_log(f"Video data: {video_info['filename']}, size: {video_info['filesize']}, timestamp: {video_info['timestamp']}", "info")
                        downloaded_videos.append(video_info)
                
                self.emit_log(f"Found {len(downloaded_videos)} currently available videos")
                return downloaded_videos
            
            else:
                # Fallback to history endpoint with better filtering
                self.emit_log("Using history endpoint as fallback...")
                history_url = f"{metube_url.rstrip('/')}/history"
                response = self.session.get(history_url)
                response.raise_for_status()
                
                history_data = response.json()
                downloaded_videos = []
                
                if 'done' in history_data:
                    for video in history_data['done']:
                        # More flexible validation for channel-based folder structure
                        filename = video.get('filename', '')
                        filesize = video.get('filesize')
                        status = video.get('status', '')
                        
                        # Check if this appears to be a valid completed download
                        is_valid_download = (
                            filename and                    # Has a filename
                            status not in ['error', 'failed', 'cancelled'] and  # Not failed
                            (filesize is None or filesize > 0)  # Either no size info or positive size
                        )
                        
                        if is_valid_download:
                            video_info = {
                                'id': video.get('id'),
                                'title': video.get('title', 'Unknown Title'),
                                'url': video.get('url'),
                                'filename': filename,
                                'timestamp': video.get('timestamp'),
                                'filesize': filesize,
                                'status': status,
                                'folder': video.get('folder', ''),  # Channel folder if available
                                'filepath': video.get('filepath', filename)  # Full path or just filename
                            }
                            downloaded_videos.append(video_info)
                
                total_history = len(history_data.get('done', []))
                self.emit_log(f"Found {len(downloaded_videos)} available videos from {total_history} history entries")
                
                if len(downloaded_videos) == 0 and total_history > 0:
                    self.emit_log("All videos in history appear to have been deleted from storage", "warning")
                
                return downloaded_videos
            
        except Exception as e:
            self.emit_log(f"Error fetching downloaded videos: {e}", "error")
            return []
    
    def delete_video(self, metube_url, video_id, filename, filepath=None):
        """Delete a downloaded video from MeTube."""
        try:
            display_name = filepath or filename
            self.emit_log(f"Deleting video: {display_name}")
            
            # Use MeTube's delete API
            delete_url = f"{metube_url.rstrip('/')}/delete"
            
            # Try using the full filepath first, then fall back to video_id
            delete_identifiers = []
            if filepath and filepath != filename:
                delete_identifiers.append(filepath)
            if video_id:
                delete_identifiers.append(video_id)
            if filename:
                delete_identifiers.append(filename)
            
            # Try each identifier until one works
            for identifier in delete_identifiers:
                try:
                    data = {
                        "ids": [identifier],
                        "where": "done"
                    }
                    
                    response = self.session.post(delete_url, json=data)
                    response.raise_for_status()
                    
                    result = response.json()
                    if result.get('status') == 'ok':
                        self.emit_log(f"Successfully deleted: {display_name}")
                        return True
                except Exception as delete_error:
                    self.emit_log(f"Delete attempt with {identifier} failed: {delete_error}", "warning")
                    continue
            
            self.emit_log(f"All delete attempts failed for: {display_name}", "error")
            return False
                
        except Exception as e:
            self.emit_log(f"Error deleting video {filename}: {e}", "error")
            return False
    
    def clear_metube_history(self, metube_url):
        """Clear MeTube download history."""
        try:
            self.emit_log("Clearing MeTube download history...")
            
            # Use MeTube's clear/clean endpoint if available
            clear_url = f"{metube_url.rstrip('/')}/clear"
            response = self.session.post(clear_url)
            
            if response.status_code in [200, 201, 404]:  # 404 means endpoint doesn't exist
                if response.status_code == 404:
                    self.emit_log("Clear endpoint not available on this MeTube version", "warning")
                    return False
                else:
                    self.emit_log("Successfully cleared MeTube history")
                    return True
            else:
                self.emit_log(f"Failed to clear history: {response.status_code}", "error")
                return False
                
        except Exception as e:
            self.emit_log(f"Error clearing history: {e}", "error")
            return False
    
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

@socketio.on('fetch_downloaded')
def handle_fetch_downloaded(data):
    if handler.is_running:
        emit('error', {'message': 'Operation already in progress'})
        return
    
    handler.is_running = True
    emit('operation_started')
    
    def fetch_downloaded_thread():
        try:
            videos = handler.get_downloaded_videos(data['metube_url'])
            socketio.emit('downloaded_videos', {'videos': videos})
        finally:
            handler.is_running = False
            socketio.emit('operation_finished')
    
    thread = threading.Thread(target=fetch_downloaded_thread)
    thread.daemon = True
    thread.start()

@socketio.on('delete_video')
def handle_delete_video(data):
    if handler.is_running:
        emit('error', {'message': 'Operation already in progress'})
        return
    
    handler.is_running = True
    emit('operation_started')
    
    def delete_video_thread():
        try:
            success = handler.delete_video(
                data['metube_url'],
                data['video_id'], 
                data['filename'],
                data.get('filepath')  # Include filepath for channel-based structure
            )
            socketio.emit('video_deleted', {
                'video_id': data['video_id'],
                'success': success
            })
        finally:
            handler.is_running = False
            socketio.emit('operation_finished')
    
    thread = threading.Thread(target=delete_video_thread)
    thread.daemon = True
    thread.start()

@socketio.on('clear_history')
def handle_clear_history(data):
    if handler.is_running:
        emit('error', {'message': 'Operation already in progress'})
        return
    
    handler.is_running = True
    emit('operation_started')
    
    def clear_history_thread():
        try:
            success = handler.clear_metube_history(data['metube_url'])
            socketio.emit('history_cleared', {'success': success})
        finally:
            handler.is_running = False
            socketio.emit('operation_finished')
    
    thread = threading.Thread(target=clear_history_thread)
    thread.daemon = True
    thread.start()

@socketio.on('connect')
def handle_connect():
    emit('connected', {'data': 'Connected to YouTube to MeTube server'})

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5001)