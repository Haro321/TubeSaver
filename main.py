import yt_dlp
import customtkinter as ctk
import threading
import os
import subprocess
import re

class GUI:
    def __init__(self):
        self.quality_mapping = {
            '360p': 360,
            '480p': 480,
            '720p': 720,
            '1080p': 1080,
            '1440p': 1440,
            '4K': 2160,
            'Highest': 'best',
            'Audio Only': 'bestaudio'
        }
        self.base_path = "./%(title)s.%(ext)s"  
        self.window = ctk.CTk()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.window.title("TubeSaver")
        self.window.geometry("500x300")
        self.window.resizable(False, False)
        
        self.title_label = ctk.CTkLabel(
            self.window, text="TubeSaver - YouTube Downloader", font=("Arial", 18, "bold")
        )
        self.title_label.pack(pady=(20, 10))
        
        self.linkEntry = ctk.CTkEntry(
            self.window, width=400, placeholder_text="Enter the YouTube link here"
        )
        self.linkEntry.pack(pady=(5, 10))

        self.comboBox = ctk.CTkComboBox(
            self.window, values=list(self.quality_mapping.keys()), width=200
        )
        self.comboBox.set("Select Quality") 
        self.comboBox.pack(pady=(0, 10))

        self.downloadButton = ctk.CTkButton(
            self.window, text="Start Download", command=self.start_download_thread, width=150
        )
        self.downloadButton.pack(pady=(10, 20))

        self.progress = ctk.CTkLabel(self.window, text="Progress: Waiting...", font=("Arial", 14))
        self.progress.pack(pady=(10, 20))
        
        self.window.mainloop()
    
    def show_popup(self, text):
        popup = ctk.CTkToplevel(self.window)
        popup.title("Error")
        popup.geometry("300x150")
        popup.resizable(False, False)

        message = ctk.CTkLabel(popup, text=text, wraplength=250, justify="center", font=("Arial", 12))
        message.pack(pady=20)

        close_button = ctk.CTkButton(popup, text="Close", command=popup.destroy)
        close_button.pack(pady=10)

        popup.transient(self.window)
        popup.grab_set()
        popup.lift()
        popup.attributes('-topmost', True)
        popup.wait_window()

    def start_download_thread(self):
        thread = threading.Thread(target=self.download)
        thread.daemon = True
        thread.start()

    def download(self):
        url = self.linkEntry.get().strip()
        
        if not url:
            self.show_popup("Please enter a valid YouTube URL.")
            return

        selected_quality = self.comboBox.get()
        
        if selected_quality in self.quality_mapping:
            try:
                with yt_dlp.YoutubeDL() as ydl:
                    info_dict = ydl.extract_info(url, download=False) 
                    title = info_dict.get('title', 'video')  
                    title = self.sanitize_title(title)  

                temp_video_file = self.base_path.replace('%(title)s', title).replace('%(ext)s', 'mp4')
                temp_audio_file = self.base_path.replace('%(title)s', title).replace('%(ext)s', 'm4a')
                final_file = self.base_path.replace('%(title)s', title).replace('%(ext)s', 'final_video.mp4')

                video_ydl_opts = {
                    'format': f'bestvideo[height<={self.quality_mapping[selected_quality]}]',
                    'outtmpl': temp_video_file,
                    'progress_hooks': [self.progress_hook],
                    'no_color': True,
                    'noplaylist': True,
                    'verbose': True,
                }
                
                audio_ydl_opts = {
                    'format': 'bestaudio',
                    'outtmpl': temp_audio_file,
                    'progress_hooks': [self.progress_hook],
                    'no_color': True,
                    'noplaylist': True,
                    'verbose': True,
                }

                self.progress.configure(text="Progress: Waiting...")

                with yt_dlp.YoutubeDL(video_ydl_opts) as video_ydl:
                    video_ydl.download([url])
                with yt_dlp.YoutubeDL(audio_ydl_opts) as audio_ydl:
                    audio_ydl.download([url])
                
                if os.path.exists(temp_video_file) and os.path.exists(temp_audio_file):
                    if self.merge_files(temp_video_file, temp_audio_file, final_file):
                        self.progress.configure(text=f"Progress: Download and merge completed! Saved to {final_file}")
                    else:
                        self.show_popup("Error during merging files.")
                else:
                    self.show_popup("Error: Downloaded files not found.")
            except Exception as e:
                self.show_popup(text=f"Error: {e}")
        else:
            self.show_popup("Please select a valid quality option.")

    def sanitize_title(self, title):
        title = re.sub(r'[^\w\s-]', '', title)  
        title = re.sub(r'[-\s]+', '_', title)  
        return title.strip('_')  

    def merge_files(self, video_file, audio_file, final_file):
        if not self.is_ffmpeg_installed():
            self.show_popup("FFmpeg is not installed. Please install FFmpeg to merge files.")
            return False

        ffmpeg_command = f'ffmpeg -i "{video_file}" -i "{audio_file}" -c:v copy -c:a aac -strict experimental "{final_file}"'
        try:
            subprocess.run(ffmpeg_command, shell=True, check=True)
            os.remove(video_file)
            os.remove(audio_file)
            return True
        except subprocess.CalledProcessError:
            return False

    def is_ffmpeg_installed(self):
        try:
            subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except FileNotFoundError:
            return False

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            percentage = d.get('_percent_str', '0%').split()[0]
            self.progress.configure(text=f"Progress: {percentage} downloaded")
        elif d['status'] == 'finished':
            self.progress.configure(text="Progress: Download completed!")

if __name__ == "__main__":
    GUI()
