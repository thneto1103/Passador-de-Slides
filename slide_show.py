"""
Photo Slide Show Application
Displays photos from a folder structure in sequential or random mode.
"""

import os
import random
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from pathlib import Path
import time


class SlideShow:
    def __init__(self, root):
        self.root = root
        self.root.title("Photo Slide Show")
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg='black')
        
        # Variables
        self.photos_folders = []  # List of selected folders
        self.image_files = []
        self.current_index = 0
        self.is_random_mode = False
        self.display_duration = 3000  # milliseconds (default)
        self.min_duration = 500  # Fastest (0.5 seconds)
        self.max_duration = 10000  # Slowest (10 seconds)
        self.transition_duration = 500  # milliseconds
        
        # History for random mode navigation
        self.random_sequence = []  # Complete sequence of visited indices in random mode
        self.random_sequence_position = -1  # Current position in sequence (-1 means at the end)
        
        # Mouse movement tracking for auto-hide controls
        self.fade_timer = None
        self.fade_delay = 3500  # milliseconds (3.5 seconds)
        self.control_visible = False
        self.fade_alpha = 1.0  # Opacity level for fade effect
        
        # Debounce for keyboard events to prevent double-triggering
        self.last_key_time = {}
        self.key_debounce_delay = 300  # milliseconds (increased to prevent key repeat)
        self.navigation_locked = False  # Lock to prevent simultaneous navigation
        
        # Create canvas for image display
        self.canvas = tk.Canvas(self.root, bg='black', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.focus_set()  # Make canvas focusable to receive keyboard events
        
        # Bind keys - use KeyRelease for arrow keys to avoid key repeat issues
        self.canvas.bind('<KeyPress-Escape>', self.quit_fullscreen)
        self.canvas.bind('<KeyPress-space>', self.toggle_mode)
        self.canvas.bind('<KeyRelease-Left>', self.debounced_previous_image)  # Use KeyRelease to avoid key repeat
        self.canvas.bind('<KeyRelease-Right>', self.debounced_next_image)  # Use KeyRelease to avoid key repeat
        self.canvas.bind('<KeyPress-r>', self.toggle_random_mode)
        self.canvas.bind('<KeyPress-R>', self.toggle_random_mode)
        self.canvas.bind('<KeyPress-f>', self.toggle_fullscreen)
        self.canvas.bind('<KeyPress-F>', self.toggle_fullscreen)
        
        # Also bind to root for when canvas doesn't have focus
        self.root.bind('<KeyPress-Escape>', self.quit_fullscreen)
        self.root.bind('<KeyPress-space>', self.toggle_mode)
        self.root.bind('<KeyRelease-Left>', self.debounced_previous_image)  # Use KeyRelease to avoid key repeat
        self.root.bind('<KeyRelease-Right>', self.debounced_next_image)  # Use KeyRelease to avoid key repeat
        self.root.bind('<KeyPress-r>', self.toggle_random_mode)
        self.root.bind('<KeyPress-R>', self.toggle_random_mode)
        self.root.bind('<KeyPress-f>', self.toggle_fullscreen)
        self.root.bind('<KeyPress-F>', self.toggle_fullscreen)
        
        # Bind all key events to canvas to keep focus
        self.canvas.bind('<Button-1>', lambda e: self.canvas.focus_set())
        
        # Bind mouse movement for auto-hide controls
        self.root.bind('<Motion>', self.on_mouse_move)
        self.canvas.bind('<Motion>', self.on_mouse_move)
        self.root.bind('<Enter>', self.on_mouse_move)  # Show when mouse enters window
        
        # Control panel (must be created before select_photos_folder)
        self.create_control_panel()
        
        # Start with controls hidden
        self.hide_controls()
        
        # Start by asking for photos folder
        self.select_photos_folder()
        
    def create_control_panel(self):
        """Create a control panel with buttons at the bottom"""
        self.control_frame = tk.Frame(self.root, bg='black')
        self.control_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        
        # Status label at top
        self.status_label = tk.Label(
            self.control_frame,
            text="",
            bg='black',
            fg='white',
            font=('Arial', 12, 'bold')
        )
        self.status_label.pack(pady=5)
        
        # Speed control slider (only visible when auto mode is on)
        speed_frame = tk.Frame(self.control_frame, bg='black')
        speed_frame.pack(pady=5, fill=tk.X, padx=20)
        
        speed_label = tk.Label(
            speed_frame,
            text="Speed:",
            bg='black',
            fg='white',
            font=('Arial', 10)
        )
        speed_label.pack(side=tk.LEFT, padx=5)
        
        # Speed slider (0-100, where 0 is slowest, 100 is fastest)
        # We'll invert it so higher value = faster (lower duration)
        # Calculate initial slider value from default duration (3000ms)
        # Formula: slider = 100 * (1 - (duration - min) / (max - min))
        initial_slider = 100 * (1 - (self.display_duration - self.min_duration) / (self.max_duration - self.min_duration))
        self.speed_var = tk.DoubleVar()
        self.speed_var.set(initial_slider)  # Default to middle speed (3000ms)
        
        self.speed_slider = tk.Scale(
            speed_frame,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            variable=self.speed_var,
            bg='#2a2a2a',
            fg='white',
            troughcolor='#1a1a1a',
            activebackground='#555555',
            length=300,
            command=self.update_speed
        )
        self.speed_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        
        # Initialize speed label with current duration
        initial_speed_seconds = self.display_duration / 1000.0
        self.speed_value_label = tk.Label(
            speed_frame,
            text=f"{initial_speed_seconds:.1f}s",
            bg='black',
            fg='white',
            font=('Arial', 10),
            width=6
        )
        self.speed_value_label.pack(side=tk.LEFT, padx=5)
        
        # Button frame
        button_frame = tk.Frame(self.control_frame, bg='black')
        button_frame.pack(pady=10)
        
        # Button style
        button_style = {
            'bg': '#333333',
            'fg': 'white',
            'font': ('Arial', 11, 'bold'),
            'relief': tk.RAISED,
            'bd': 2,
            'padx': 15,
            'pady': 8,
            'cursor': 'hand2'
        }
        
        # Previous button
        self.prev_button = tk.Button(
            button_frame,
            text="← Previous",
            command=self.previous_image,
            **button_style
        )
        self.prev_button.pack(side=tk.LEFT, padx=5)
        
        # Auto-Advance button
        self.auto_advance_button = tk.Button(
            button_frame,
            text="⏭ Auto [OFF]",
            command=self.toggle_auto_advance,
            **button_style
        )
        self.auto_advance_button.pack(side=tk.LEFT, padx=5)
        
        # Pause/Resume button
        self.pause_button = tk.Button(
            button_frame,
            text="⏸ Pause",
            command=self.toggle_mode,
            **button_style
        )
        self.pause_button.pack(side=tk.LEFT, padx=5)
        
        # Random Mode button
        self.random_button = tk.Button(
            button_frame,
            text="🎲 Random",
            command=self.toggle_random_mode,
            **button_style
        )
        self.random_button.pack(side=tk.LEFT, padx=5)
        
        # Fullscreen button
        self.fullscreen_button = tk.Button(
            button_frame,
            text="⛶ Fullscreen",
            command=self.toggle_fullscreen,
            **button_style
        )
        self.fullscreen_button.pack(side=tk.LEFT, padx=5)
        
        # Next button
        self.next_button = tk.Button(
            button_frame,
            text="Next →",
            command=self.next_image,
            **button_style
        )
        self.next_button.pack(side=tk.LEFT, padx=5)
        
        # Quit button
        self.quit_button = tk.Button(
            button_frame,
            text="✕ Quit",
            command=self.quit_fullscreen,
            bg='#660000',
            fg='white',
            font=('Arial', 11, 'bold'),
            relief=tk.RAISED,
            bd=2,
            padx=15,
            pady=8,
            cursor='hand2'
        )
        self.quit_button.pack(side=tk.LEFT, padx=5)
        
        # Update button hover effects
        def on_enter(btn, default_bg):
            return lambda e: btn.config(bg='#555555' if default_bg != '#660000' else '#880000')
        
        def on_leave(btn, default_bg):
            return lambda e: btn.config(bg=default_bg)
        
        for btn, default_bg in [(self.prev_button, '#333333'),
                                (self.auto_advance_button, '#333333'),
                                (self.pause_button, '#333333'),
                                (self.random_button, '#333333'),
                                (self.fullscreen_button, '#333333'),
                                (self.next_button, '#333333'),
                                (self.quit_button, '#660000')]:
            btn.bind('<Enter>', on_enter(btn, default_bg))
            btn.bind('<Leave>', on_leave(btn, default_bg))
        
        # Bind mouse events to control panel to keep it visible when hovering
        self.control_frame.bind('<Enter>', self.on_mouse_move)
        self.control_frame.bind('<Motion>', self.on_mouse_move)
        for widget in [self.status_label, button_frame] + [
            self.prev_button, self.auto_advance_button, self.pause_button,
            self.random_button, self.fullscreen_button, self.next_button, self.quit_button
        ]:
            widget.bind('<Enter>', self.on_mouse_move)
            widget.bind('<Motion>', self.on_mouse_move)
    
    def on_mouse_move(self, event=None):
        """Show controls when mouse moves and reset fade timer"""
        if not self.control_visible:
            self.show_controls()
        self.reset_fade_timer()
    
    def reset_fade_timer(self):
        """Reset the timer that hides controls after mouse stops moving"""
        if self.fade_timer:
            self.root.after_cancel(self.fade_timer)
        self.fade_timer = self.root.after(self.fade_delay, self.start_fade_out)
    
    def start_fade_out(self):
        """Start fading out the controls"""
        if not self.control_visible:
            return
        self.fade_out_step()
    
    def fade_out_step(self, step=0):
        """Gradually fade out controls by reducing color intensity"""
        if not self.control_visible:
            return
        
        if step >= 15:  # 15 steps for smooth fade (~750ms total)
            self.hide_controls()
            return
        
        # Calculate opacity (1.0 to 0.0)
        opacity = 1.0 - (step / 15.0)
        
        # Fade colors by interpolating between original and black
        # Background colors fade from original to black
        # Text colors fade from white to darker shades
        fade_factor = int(255 * opacity)
        if fade_factor < 30:  # Too dark to see, hide
            self.hide_controls()
            return
        
        # Convert fade_factor to hex for color
        fade_hex = format(min(fade_factor, 255), '02x')
        
        # Update control frame background (black fades to... black, so we'll fade text instead)
        # Fade text colors from white to gray
        text_color = f'#{fade_hex}{fade_hex}{fade_hex}'
        bg_color = '#000000'  # Keep black background
        
        # Update colors of control panel widgets
        try:
            self.control_frame.config(bg=bg_color)
            self.status_label.config(fg=text_color, bg=bg_color)
            
            # Get all buttons and fade their text
            for widget in self.control_frame.winfo_children():
                if isinstance(widget, tk.Frame):
                    for btn in widget.winfo_children():
                        if isinstance(btn, tk.Button):
                            # Keep button backgrounds but fade text slightly
                            current_bg = btn.cget('bg')
                            if current_bg != '#006600' and current_bg != '#660000':  # Don't fade colored states
                                btn.config(fg=text_color)
        except:
            pass  # Ignore errors during fade
        
        # Schedule next fade step (each step is 50ms)
        if step < 15:
            self.root.after(50, lambda: self.fade_out_step(step + 1))
    
    def show_controls(self):
        """Show the control panel with full opacity"""
        self.control_visible = True
        self.control_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        
        # Reset all colors to full opacity
        self.control_frame.config(bg='black')
        self.status_label.config(fg='white', bg='black')
        
        # Reset button colors
        button_style_fg = 'white'
        try:
            for widget in self.control_frame.winfo_children():
                if isinstance(widget, tk.Frame):
                    for btn in widget.winfo_children():
                        if isinstance(btn, tk.Button):
                            btn.config(fg=button_style_fg)
        except:
            pass
        
        self.root.update_idletasks()
    
    def hide_controls(self):
        """Hide the control panel"""
        self.control_visible = False
        self.control_frame.pack_forget()
        if self.fade_timer:
            self.root.after_cancel(self.fade_timer)
            self.fade_timer = None
        
    def select_photos_folder(self):
        """Dialog to select one or more Photos folders"""
        # Create a custom dialog for selecting multiple folders
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Photo Folders")
        dialog.geometry("600x400")
        dialog.configure(bg='#1a1a1a')
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (dialog.winfo_screenheight() // 2) - (400 // 2)
        dialog.geometry(f"600x400+{x}+{y}")
        
        # Title label
        title_label = tk.Label(
            dialog,
            text="Select Photo Folders",
            bg='#1a1a1a',
            fg='white',
            font=('Arial', 14, 'bold'),
            pady=10
        )
        title_label.pack()
        
        # Listbox with scrollbar for selected folders
        list_frame = tk.Frame(dialog, bg='#1a1a1a')
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        folders_listbox = tk.Listbox(
            list_frame,
            bg='#2a2a2a',
            fg='white',
            font=('Arial', 10),
            selectmode=tk.SINGLE,
            yscrollcommand=scrollbar.set,
            height=12
        )
        folders_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=folders_listbox.yview)
        
        # Load existing folders if any
        for folder in self.photos_folders:
            folders_listbox.insert(tk.END, str(folder))
        
        # Button frame
        button_frame = tk.Frame(dialog, bg='#1a1a1a')
        button_frame.pack(pady=10)
        
        def add_folder():
            folder = filedialog.askdirectory(title="Select Photo Folder")
            if folder:
                folder_path = Path(folder)
                if folder_path not in self.photos_folders:
                    self.photos_folders.append(folder_path)
                    folders_listbox.insert(tk.END, str(folder_path))
                else:
                    messagebox.showinfo("Already Added", f"Folder '{folder_path.name}' is already in the list.")
        
        def remove_folder():
            selection = folders_listbox.curselection()
            if selection:
                index = selection[0]
                folder_str = folders_listbox.get(index)
                # Find and remove from list
                folder_path = Path(folder_str)
                if folder_path in self.photos_folders:
                    self.photos_folders.remove(folder_path)
                folders_listbox.delete(index)
            else:
                messagebox.showinfo("No Selection", "Please select a folder to remove.")
        
        # Buttons
        add_btn = tk.Button(
            button_frame,
            text="+ Add Folder",
            command=add_folder,
            bg='#006600',
            fg='white',
            font=('Arial', 11, 'bold'),
            padx=15,
            pady=5,
            cursor='hand2'
        )
        add_btn.pack(side=tk.LEFT, padx=5)
        
        remove_btn = tk.Button(
            button_frame,
            text="- Remove Selected",
            command=remove_folder,
            bg='#660000',
            fg='white',
            font=('Arial', 11, 'bold'),
            padx=15,
            pady=5,
            cursor='hand2'
        )
        remove_btn.pack(side=tk.LEFT, padx=5)
        
        def finish_selection():
            if self.photos_folders:
                dialog.destroy()
                self.load_images()
                if self.image_files:
                    self.start_slideshow()
                else:
                    messagebox.showwarning(
                        "No Images Found",
                        "No image files found in the selected folders."
                    )
            else:
                response = messagebox.askyesno(
                    "No Folders Selected",
                    "No folders selected. Would you like to select at least one folder to continue?"
                )
                if not response:
                    dialog.destroy()
                    self.root.quit()
        
        finish_btn = tk.Button(
            button_frame,
            text="✓ Done",
            command=finish_selection,
            bg='#004488',
            fg='white',
            font=('Arial', 11, 'bold'),
            padx=15,
            pady=5,
            cursor='hand2'
        )
        finish_btn.pack(side=tk.LEFT, padx=5)
        
        # Instructions
        instructions_text = (
            "📁 You can select a parent folder (e.g., 'Photo') that contains multiple subfolders (e.g., 'Photos2003', 'PhotosFromCamp').\n"
            "The app will automatically scan ALL subfolders and their contents recursively.\n"
            "💡 Tip: Click 'Add Folder' to select parent folders. All images in subfolders will be included automatically."
        )
        info_label = tk.Label(
            dialog,
            text=instructions_text,
            bg='#1a1a1a',
            fg='#cccccc',
            font=('Arial', 9),
            wraplength=550,
            justify=tk.LEFT
        )
        info_label.pack(pady=10, padx=20)
        
        # Example structure label
        example_label = tk.Label(
            dialog,
            text="Example structure:\nPhoto/ → Photos2003/ (photo1.jpg, photo2.jpg...)\n      → PhotosFromCamp/ (photo1.jpg, photo2.jpg...)\n\nSelect 'Photo' folder and all subfolders will be scanned!",
            bg='#1a1a1a',
            fg='#88cc88',
            font=('Courier', 8),
            justify=tk.LEFT,
            wraplength=550
        )
        example_label.pack(pady=5, padx=20)
        
        # Focus on dialog
        dialog.focus_set()
    
    def load_images(self):
        """Load all image files from all selected folder structures"""
        self.image_files = []
        supported_formats = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif'}
        
        if not self.photos_folders:
            return
        
        # Recursively search for images in all selected folders and their subfolders
        for photos_folder in self.photos_folders:
            if not photos_folder.exists():
                print(f"Warning: Folder does not exist: {photos_folder}")
                continue
            
            for root, dirs, files in os.walk(photos_folder):
                for file in files:
                    file_path = Path(root) / file
                    if file_path.suffix.lower() in supported_formats:
                        try:
                            # Verify it's a valid image
                            img = Image.open(file_path)
                            img.verify()
                            self.image_files.append(str(file_path))
                        except Exception:
                            continue
        
        # Sort files for sequential mode (by folder then filename)
        if self.image_files and not self.is_random_mode:
            self.image_files.sort()
        
        total_images = len(self.image_files)
        folder_count = len(self.photos_folders)
        folder_names = [f.name for f in self.photos_folders]
        print(f"Loaded {total_images} images from {folder_count} folder(s): {', '.join(folder_names)}")
    
    def get_display_size(self):
        """Get screen size for fullscreen display"""
        self.root.update_idletasks()
        return self.root.winfo_width(), self.root.winfo_height()
    
    def resize_image(self, image_path):
        """Resize image to fit screen while maintaining aspect ratio"""
        try:
            img = Image.open(image_path)
            
            # Convert RGBA to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (0, 0, 0))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Get screen size
            screen_width, screen_height = self.get_display_size()
            
            # Calculate new size maintaining aspect ratio
            img_width, img_height = img.size
            scale = min(screen_width / img_width, screen_height / img_height)
            
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            return img
        except Exception as e:
            print(f"Error loading image {image_path}: {e}")
            return None
    
    def display_image(self, image_path, transition=True):
        """Display image on canvas"""
        if not image_path:
            return
        
        img = self.resize_image(image_path)
        if img is None:
            return
        
        # Convert to PhotoImage
        photo = ImageTk.PhotoImage(img)
        
        # Clear canvas and display new image
        self.canvas.delete("all")
        
        # Center the image
        screen_width, screen_height = self.get_display_size()
        x = (screen_width - photo.width()) // 2
        y = (screen_height - photo.height()) // 2
        
        self.canvas.create_image(x, y, anchor=tk.NW, image=photo)
        self.canvas.image = photo  # Keep a reference
        
        # Ensure canvas has focus for keyboard events
        self.canvas.focus_set()
        
        # Update status
        folder_name = Path(image_path).parent.name
        status_text = f"Image {self.current_index + 1}/{len(self.image_files)} | Folder: {folder_name}"
        if self.is_random_mode:
            status_text += " | [RANDOM MODE]"
        self.status_label.config(text=status_text)
    
    def debounced_next_image(self, event=None):
        """Debounced wrapper for next_image to prevent double-triggering"""
        # Check if navigation is locked (prevent simultaneous execution)
        if self.navigation_locked:
            return
        
        import time
        current_time = time.time() * 1000  # Convert to milliseconds
        key = 'Right'
        
        if key in self.last_key_time:
            time_since_last = current_time - self.last_key_time[key]
            if time_since_last < self.key_debounce_delay:
                return  # Ignore if too soon after last press
        
        self.last_key_time[key] = current_time
        self.navigation_locked = True  # Lock navigation
        
        try:
            self.next_image(event)
        finally:
            # Unlock after a short delay to allow next navigation
            self.root.after(self.key_debounce_delay, lambda: setattr(self, 'navigation_locked', False))
    
    def debounced_previous_image(self, event=None):
        """Debounced wrapper for previous_image to prevent double-triggering"""
        # Check if navigation is locked (prevent simultaneous execution)
        if self.navigation_locked:
            return
        
        import time
        current_time = time.time() * 1000  # Convert to milliseconds
        key = 'Left'
        
        if key in self.last_key_time:
            time_since_last = current_time - self.last_key_time[key]
            if time_since_last < self.key_debounce_delay:
                return  # Ignore if too soon after last press
        
        self.last_key_time[key] = current_time
        self.navigation_locked = True  # Lock navigation
        
        try:
            self.previous_image(event)
        finally:
            # Unlock after a short delay to allow next navigation
            self.root.after(self.key_debounce_delay, lambda: setattr(self, 'navigation_locked', False))
    
    def next_image(self, event=None):
        """Go to next image"""
        if not self.image_files:
            return
        
        if self.is_random_mode:
            # Check if we're in the middle of the sequence (went back before)
            if self.random_sequence_position >= 0 and self.random_sequence_position < len(self.random_sequence) - 1:
                # We're in the middle - continue the existing sequence
                self.random_sequence_position += 1
                self.current_index = self.random_sequence[self.random_sequence_position]
            else:
                # We're at the end - add current to sequence if not already there, then get new random
                if not self.random_sequence or self.random_sequence[-1] != self.current_index:
                    self.random_sequence.append(self.current_index)
                    self.random_sequence_position = len(self.random_sequence) - 1
                
                # Get next random image
                new_index = random.randint(0, len(self.image_files) - 1)
                # Avoid showing the same image immediately
                while new_index == self.current_index and len(self.image_files) > 1:
                    new_index = random.randint(0, len(self.image_files) - 1)
                
                # Add the new index to sequence
                self.current_index = new_index
                self.random_sequence.append(self.current_index)
                # Keep only last 15 items in sequence
                if len(self.random_sequence) > 15:
                    # Adjust position if we trimmed from the beginning
                    trim_count = len(self.random_sequence) - 15
                    self.random_sequence = self.random_sequence[-15:]
                    self.random_sequence_position = len(self.random_sequence) - 1
                else:
                    self.random_sequence_position = len(self.random_sequence) - 1
        else:
            self.current_index = (self.current_index + 1) % len(self.image_files)
            # Clear random sequence when in sequential mode
            self.random_sequence = []
            self.random_sequence_position = -1
        
        image_path = self.image_files[self.current_index]
        self.display_image(image_path)
        
        # Reschedule next slide only if auto-advance is enabled
        if hasattr(self, 'slideshow_running') and self.slideshow_running:
            self.pending_timer = self.root.after(int(self.display_duration), self.next_image)
    
    def previous_image(self, event=None):
        """Go to previous image"""
        if not self.image_files:
            return
        
        if self.is_random_mode:
            # Add current index to sequence if we're at the end
            if self.random_sequence_position == -1 or self.random_sequence_position == len(self.random_sequence) - 1:
                if not self.random_sequence or self.random_sequence[-1] != self.current_index:
                    self.random_sequence.append(self.current_index)
                    if len(self.random_sequence) > 15:
                        # Adjust position if we trimmed from the beginning
                        trim_count = len(self.random_sequence) - 15
                        self.random_sequence = self.random_sequence[-15:]
                        self.random_sequence_position = len(self.random_sequence) - 1
                    else:
                        self.random_sequence_position = len(self.random_sequence) - 1
            
            # Go back through sequence if available
            if self.random_sequence and len(self.random_sequence) > 1:
                # Go to previous item in sequence
                if self.random_sequence_position > 0:
                    self.random_sequence_position -= 1
                    self.current_index = self.random_sequence[self.random_sequence_position]
                else:
                    # Already at the beginning of sequence, stay at first item
                    self.current_index = self.random_sequence[0]
                    self.random_sequence_position = 0
            elif self.random_sequence:
                # Only one item in sequence
                self.current_index = self.random_sequence[0]
                self.random_sequence_position = 0
            else:
                # No sequence, just pick a random one
                self.current_index = random.randint(0, len(self.image_files) - 1)
        else:
            self.current_index = (self.current_index - 1) % len(self.image_files)
            # Don't clear sequence when in sequential mode - keep it for when random mode is re-enabled
            self.random_sequence_position = -1
        
        image_path = self.image_files[self.current_index]
        self.display_image(image_path)
    
    def toggle_random_mode(self, event=None):
        """Toggle between sequential and random mode"""
        was_random = self.is_random_mode
        self.is_random_mode = not self.is_random_mode
        
        if self.is_random_mode:
            # If we're turning random mode ON (was off before), create a new sequence
            if not was_random:
                # Starting fresh - initialize sequence with current index
                self.random_sequence = [self.current_index]
                self.random_sequence_position = 0
            else:
                # Already in random mode, just ensure current index is in sequence
                if not self.random_sequence:
                    self.random_sequence = [self.current_index]
                    self.random_sequence_position = 0
                elif self.current_index in self.random_sequence:
                    # Find current position in sequence
                    self.random_sequence_position = self.random_sequence.index(self.current_index)
                else:
                    # Add current to sequence
                    self.random_sequence.append(self.current_index)
                    self.random_sequence_position = len(self.random_sequence) - 1
            
            self.random_button.config(text="🎲 Random [ON]", bg='#006600')
            self.status_label.config(text=f"[RANDOM MODE] | Total: {len(self.image_files)} images")
        else:
            # Reload images in sorted order when turning off random mode
            self.load_images()
            # Clear sequence when turning off - will create new one when turned on again
            self.random_sequence = []
            self.random_sequence_position = -1
            self.random_button.config(text="🎲 Random", bg='#333333')
            self.status_label.config(text=f"[SEQUENTIAL MODE] | Total: {len(self.image_files)} images")
        
        # Don't change the image, just update the status
        # The current image stays the same, only the mode changes
    
    def start_slideshow(self):
        """Start slideshow (manual mode by default)"""
        if not self.image_files:
            return
        
        # Default to manual mode (no auto-advance)
        self.slideshow_running = False
        image_path = self.image_files[self.current_index]
        self.display_image(image_path)
        # Don't start auto-advance - user must click Next or enable Auto
    
    def update_speed(self, value=None):
        """Update display duration based on speed slider value"""
        # Slider value is 0-100, where 0 = slowest (max_duration), 100 = fastest (min_duration)
        slider_value = self.speed_var.get()
        # Invert: 0 = slow, 100 = fast
        # Calculate duration: min_duration + (max_duration - min_duration) * (1 - slider_value/100)
        self.display_duration = self.min_duration + (self.max_duration - self.min_duration) * (1 - slider_value / 100)
        
        # Update label to show current speed
        speed_seconds = self.display_duration / 1000.0
        self.speed_value_label.config(text=f"{speed_seconds:.1f}s")
        
        # If auto-advance is running, restart with new duration
        if hasattr(self, 'slideshow_running') and self.slideshow_running:
            # Cancel any pending next_image calls
            if hasattr(self, 'pending_timer'):
                self.root.after_cancel(self.pending_timer)
            # Restart with new duration
            self.pending_timer = self.root.after(int(self.display_duration), self.next_image)
    
    def toggle_auto_advance(self, event=None):
        """Toggle auto-advance mode on/off"""
        if not hasattr(self, 'slideshow_running'):
            self.slideshow_running = False
        
        self.slideshow_running = not self.slideshow_running
        
        if self.slideshow_running:
            self.auto_advance_button.config(text="⏭ Auto [ON]", bg='#006600')
            # Start auto-advancing with current speed
            self.pending_timer = self.root.after(int(self.display_duration), self.next_image)
        else:
            self.auto_advance_button.config(text="⏭ Auto [OFF]", bg='#333333')
            # Cancel any pending timers
            if hasattr(self, 'pending_timer'):
                self.root.after_cancel(self.pending_timer)
    
    def toggle_mode(self, event=None):
        """Toggle pause/resume (deprecated - use toggle_auto_advance instead)"""
        # This function is kept for backward compatibility but does the same as toggle_auto_advance
        self.toggle_auto_advance(event)
    
    def toggle_fullscreen(self, event=None):
        """Toggle fullscreen mode"""
        self.root.attributes('-fullscreen', not self.root.attributes('-fullscreen'))
    
    def quit_fullscreen(self, event=None):
        """Exit fullscreen or quit application"""
        if self.root.attributes('-fullscreen'):
            self.root.attributes('-fullscreen', False)
        else:
            if messagebox.askokcancel("Quit", "Do you want to quit the slideshow?"):
                self.root.quit()


def main():
    root = tk.Tk()
    app = SlideShow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
