#!/usr/bin/env python3
"""
YouTube to MeTube GUI Application

A graphical interface for the YouTube to MeTube automation tool.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import queue
import sys
import time
from youtube_to_metube import YouTubeToMeTube
from youtube_channel_scraper import YouTubeChannelScraper

class YouTubeMetubeGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube to MeTube Automation")
        self.root.geometry("800x700")
        
        self.processor = None
        self.output_queue = queue.Queue()
        self.is_running = False
        
        self.setup_ui()
        self.start_output_monitor()
    
    def setup_ui(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="YouTube to MeTube Automation", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # MeTube URL
        ttk.Label(main_frame, text="MeTube URL:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.metube_url = tk.StringVar(value="http://192.168.1.76:8081")
        metube_entry = ttk.Entry(main_frame, textvariable=self.metube_url, width=50)
        metube_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # Channel URL
        ttk.Label(main_frame, text="Channel URL:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.channel_url = tk.StringVar()
        channel_entry = ttk.Entry(main_frame, textvariable=self.channel_url, width=50)
        channel_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # Test video URL
        ttk.Label(main_frame, text="Test Video URL:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.test_video_url = tk.StringVar()
        test_entry = ttk.Entry(main_frame, textvariable=self.test_video_url, width=50)
        test_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # Options frame
        options_frame = ttk.LabelFrame(main_frame, text="Options", padding="10")
        options_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        options_frame.columnconfigure(1, weight=1)
        options_frame.columnconfigure(3, weight=1)
        
        # Count
        ttk.Label(options_frame, text="Video Count:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.count = tk.StringVar(value="5")
        count_spin = ttk.Spinbox(options_frame, from_=1, to=50, textvariable=self.count, width=10)
        count_spin.grid(row=0, column=1, sticky=tk.W, pady=5, padx=(10, 20))
        
        # Quality
        ttk.Label(options_frame, text="Quality:").grid(row=0, column=2, sticky=tk.W, pady=5)
        self.quality = tk.StringVar(value="best")
        quality_combo = ttk.Combobox(options_frame, textvariable=self.quality, width=10,
                                   values=["best", "2160p", "1440p", "1080p", "720p", "480p", "worst", "audio"])
        quality_combo.grid(row=0, column=3, sticky=tk.W, pady=5, padx=(10, 0))
        
        # Format
        ttk.Label(options_frame, text="Format:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.format_type = tk.StringVar(value="any")
        format_combo = ttk.Combobox(options_frame, textvariable=self.format_type, width=10,
                                  values=["any", "mp4", "m4a", "mp3", "opus", "wav", "flac"])
        format_combo.grid(row=1, column=1, sticky=tk.W, pady=5, padx=(10, 20))
        
        # Filter option
        self.filter_content = tk.BooleanVar(value=True)
        filter_check = ttk.Checkbutton(options_frame, text="Filter out member-only, Shorts, and livestreams",
                                     variable=self.filter_content)
        filter_check.grid(row=1, column=2, columnspan=2, sticky=tk.W, pady=5, padx=(10, 0))
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=5, column=0, columnspan=3, pady=10)
        
        # Buttons
        self.fetch_btn = ttk.Button(buttons_frame, text="Fetch Videos", command=self.fetch_videos)
        self.fetch_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.submit_btn = ttk.Button(buttons_frame, text="Submit to MeTube", command=self.submit_videos)
        self.submit_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.test_btn = ttk.Button(buttons_frame, text="Test Single Video", command=self.test_single_video)
        self.test_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_btn = ttk.Button(buttons_frame, text="Clear", command=self.clear_all)
        self.clear_btn.pack(side=tk.LEFT)
        
        # Videos frame
        videos_frame = ttk.LabelFrame(main_frame, text="Found Videos", padding="10")
        videos_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        videos_frame.columnconfigure(0, weight=1)
        videos_frame.rowconfigure(0, weight=1)
        
        # Videos listbox with scrollbar
        list_frame = ttk.Frame(videos_frame)
        list_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        self.videos_listbox = tk.Listbox(list_frame, selectmode=tk.EXTENDED)
        self.videos_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        videos_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.videos_listbox.yview)
        videos_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.videos_listbox.configure(yscrollcommand=videos_scrollbar.set)
        
        # Output frame
        output_frame = ttk.LabelFrame(main_frame, text="Output", padding="10")
        output_frame.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)
        
        # Output text area
        self.output_text = scrolledtext.ScrolledText(output_frame, height=15, width=80)
        self.output_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights for resizing
        main_frame.rowconfigure(6, weight=1)
        main_frame.rowconfigure(7, weight=2)
        
        # Store video URLs
        self.video_urls = []
    
    def log_message(self, message):
        """Add a message to the output area."""
        self.output_queue.put(message)
    
    def start_output_monitor(self):
        """Monitor the output queue and update the text area."""
        try:
            while True:
                message = self.output_queue.get_nowait()
                self.output_text.insert(tk.END, message + "\n")
                self.output_text.see(tk.END)
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self.start_output_monitor)
    
    def set_buttons_state(self, state):
        """Enable or disable buttons."""
        self.fetch_btn.configure(state=state)
        self.submit_btn.configure(state=state)
        self.test_btn.configure(state=state)
    
    def fetch_videos(self):
        """Fetch videos from the specified channel."""
        channel_url = self.channel_url.get().strip()
        if not channel_url:
            messagebox.showerror("Error", "Please enter a channel URL")
            return
        
        try:
            count = int(self.count.get())
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number for video count")
            return
        
        self.set_buttons_state(tk.DISABLED)
        self.videos_listbox.delete(0, tk.END)
        self.video_urls.clear()
        
        # Run in background thread
        thread = threading.Thread(target=self._fetch_videos_thread, 
                                 args=(channel_url, count, self.filter_content.get()))
        thread.daemon = True
        thread.start()
    
    def _fetch_videos_thread(self, channel_url, count, filter_content):
        """Background thread for fetching videos."""
        try:
            self.log_message(f"Fetching {count} videos from: {channel_url}")
            if filter_content:
                self.log_message("Filtering enabled: excluding member-only, Shorts, and livestreams")
            
            scraper = YouTubeChannelScraper()
            videos = scraper.get_channel_videos(channel_url, count, filter_content)
            
            if videos:
                self.video_urls = videos
                self.root.after(0, self._update_videos_list, videos)
                self.log_message(f"Found {len(videos)} videos")
            else:
                self.log_message("No videos found")
            
        except Exception as e:
            self.log_message(f"Error fetching videos: {e}")
        finally:
            self.root.after(0, lambda: self.set_buttons_state(tk.NORMAL))
    
    def _update_videos_list(self, videos):
        """Update the videos listbox with found videos."""
        for i, video_url in enumerate(videos, 1):
            self.videos_listbox.insert(tk.END, f"{i}. {video_url}")
    
    def submit_videos(self):
        """Submit selected videos to MeTube."""
        if not self.video_urls:
            messagebox.showerror("Error", "No videos to submit. Fetch videos first.")
            return
        
        metube_url = self.metube_url.get().strip()
        if not metube_url:
            messagebox.showerror("Error", "Please enter a MeTube URL")
            return
        
        # Get selected videos or all if none selected
        selected_indices = self.videos_listbox.curselection()
        if selected_indices:
            videos_to_submit = [self.video_urls[i] for i in selected_indices]
        else:
            videos_to_submit = self.video_urls
        
        self.set_buttons_state(tk.DISABLED)
        
        # Run in background thread
        thread = threading.Thread(target=self._submit_videos_thread,
                                 args=(videos_to_submit, metube_url, 
                                      self.quality.get(), self.format_type.get()))
        thread.daemon = True
        thread.start()
    
    def _submit_videos_thread(self, videos, metube_url, quality, format_type):
        """Background thread for submitting videos to MeTube."""
        try:
            processor = YouTubeToMeTube(metube_url)
            
            self.log_message(f"Submitting {len(videos)} videos to MeTube...")
            self.log_message(f"Quality: {quality}, Format: {format_type}")
            
            successful = 0
            failed = 0
            
            for i, video_url in enumerate(videos, 1):
                self.log_message(f"[{i}/{len(videos)}] Processing: {video_url}")
                
                if processor.submit_to_metube(video_url, quality, format_type):
                    successful += 1
                    self.log_message(f"✓ Successfully submitted")
                else:
                    failed += 1
                    self.log_message(f"✗ Failed to submit")
                
                # Add delay between submissions
                if i < len(videos):
                    time.sleep(1)
            
            self.log_message(f"\n=== Summary ===")
            self.log_message(f"Successfully submitted: {successful}")
            self.log_message(f"Failed: {failed}")
            self.log_message(f"Total processed: {len(videos)}")
            
        except Exception as e:
            self.log_message(f"Error during submission: {e}")
        finally:
            self.root.after(0, lambda: self.set_buttons_state(tk.NORMAL))
    
    def test_single_video(self):
        """Test submission of a single video."""
        video_url = self.test_video_url.get().strip()
        if not video_url:
            messagebox.showerror("Error", "Please enter a test video URL")
            return
        
        metube_url = self.metube_url.get().strip()
        if not metube_url:
            messagebox.showerror("Error", "Please enter a MeTube URL")
            return
        
        self.set_buttons_state(tk.DISABLED)
        
        # Run in background thread
        thread = threading.Thread(target=self._test_single_video_thread,
                                 args=(video_url, metube_url, 
                                      self.quality.get(), self.format_type.get()))
        thread.daemon = True
        thread.start()
    
    def _test_single_video_thread(self, video_url, metube_url, quality, format_type):
        """Background thread for testing single video submission."""
        try:
            processor = YouTubeToMeTube(metube_url)
            
            self.log_message(f"Testing single video: {video_url}")
            self.log_message(f"Quality: {quality}, Format: {format_type}")
            
            if processor.submit_to_metube(video_url, quality, format_type):
                self.log_message("✓ Test submission successful")
            else:
                self.log_message("✗ Test submission failed")
                
        except Exception as e:
            self.log_message(f"Error during test: {e}")
        finally:
            self.root.after(0, lambda: self.set_buttons_state(tk.NORMAL))
    
    def clear_all(self):
        """Clear all inputs and outputs."""
        self.channel_url.set("")
        self.test_video_url.set("")
        self.videos_listbox.delete(0, tk.END)
        self.video_urls.clear()
        self.output_text.delete(1.0, tk.END)


def main():
    root = tk.Tk()
    app = YouTubeMetubeGUI(root)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\nApplication closed by user")

if __name__ == '__main__':
    main()