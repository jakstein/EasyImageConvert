import os
import tkinter as tk
from tkinter import ttk, filedialog
from tkinterdnd2 import DND_FILES, TkinterDnD
from PIL import Image, ExifTags
import pillow_avif
import pillow_jxl

# map format options to PIL format strings
format_map = {
    'png': 'PNG',
    'jpg': 'JPEG',
    'jpeg': 'JPEG',
    'bmp': 'BMP',
    'gif': 'GIF',
    'webp': 'WEBP',
    'avif': 'AVIF',
    'jxl': 'JXL'
}

# formats that support quality settings
quality_formats = {'jpg', 'jpeg', 'webp', 'avif', 'jxl'}

def convert_and_replace(file_paths, target_format, quality):
    target_format_pil = format_map[target_format.lower()]
    for file_path in file_paths:
        file_path_lower = file_path.lower()
        file_ext = os.path.splitext(file_path_lower)[1][1:] 
        if file_ext == target_format.lower():
            log_message(f"Skipping {file_path}, already in {target_format.upper()} format.")
            continue
        
        if file_path_lower.endswith(('.webp', '.jpg', '.jpeg', '.png', '.bmp', '.gif', '.avif', '.jxl')):
            try:
                # open the image file
                img = Image.open(file_path)
                
                # preserve EXIF data
                exif_data = img.info.get('exif')
                
                # check if image has an alpha channel and remove it for JPEG
                if target_format.lower() == 'jpg' and img.mode in ('RGBA', 'LA'):
                    # Create a white background image and paste the image onto it
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[3])  # 3 is the alpha channel
                    img = background

                # create the new file path with the chosen extension
                new_file_path = file_path.rsplit('.', 1)[0] + f'.{target_format.lower()}'
                
                # sve the image in the chosen format with quality and EXIF data if available
                save_args = {}
                if target_format.lower() in quality_formats:
                    save_args['quality'] = quality
                if exif_data:
                    save_args['exif'] = exif_data
                img.save(new_file_path, target_format_pil, **save_args)
                log_message(f"Converted {file_path} to {new_file_path} with quality {quality}")

                if overwrite_var.get():
                    # delete the original file if overwrite_var is True
                    os.remove(file_path)

            except Exception as e:
                log_message(f"Error processing {file_path}: {e}")
        else:
            log_message(f"Skipping {file_path}, not a supported image format.")

def process_directory(directory, target_format, quality):
    # recursive search for files
    for root_dir, _, files in os.walk(directory):
        file_paths = [os.path.join(root_dir, file) for file in files]
        convert_and_replace(file_paths, target_format, quality)

def drop(event): # drag and drop
    file_paths = root.tk.splitlist(event.data)
    target_format = format_var.get()
    quality = int(quality_var.get())
    convert_and_replace(file_paths, target_format, quality)

def open_folder(): # open folder dialog
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        target_format = format_var.get()
        quality = int(quality_var.get())
        process_directory(folder_selected, target_format, quality)

def log_message(message):
    log_window.config(state=tk.NORMAL)
    log_window.insert(tk.END, message + "\n")
    log_window.config(state=tk.DISABLED)
    log_window.yview(tk.END)

def on_format_change(*args):
    selected_format = format_var.get().lower()
    if selected_format in quality_formats:
        quality_frame.pack(side=tk.TOP, pady=5)
    else:
        quality_frame.pack_forget()

def on_quality_change(event):
    quality_value_label.config(text=f"Quality: {int(quality_var.get())}")

# create the main application window and apply fancy colors (probably messed up)
root = TkinterDnD.Tk()
root.title("Image Converter")
root.geometry("400x450")
quality_frame = ttk.Frame(root)
quality_label = ttk.Label(quality_frame, text="Quality:")
quality_label.pack(side=tk.LEFT, padx=5)
quality_var = tk.IntVar()
quality_slider = ttk.Scale(quality_frame, from_=0, to=100, variable=quality_var, orient=tk.HORIZONTAL)
quality_slider.pack(side=tk.LEFT, padx=5)
quality_value_label = ttk.Label(quality_frame, text="Quality: 0")
quality_value_label.pack(side=tk.LEFT, padx=5)
style = ttk.Style()
style.theme_use('clam')  
style.configure('TLabel', background='#1f1f1f', foreground='white', font=('Helvetica', 10))
style.configure('TButton', background='#4a4a4a', foreground='white', font=('Helvetica', 10), relief='flat')
style.configure('TOptionMenu', background='#4a4a4a', foreground='white', font=('Helvetica', 10))
style.configure('TText', background='#2b2b2b', foreground='white')

root.configure(bg='#2b2b2b')

drop_area = tk.Label(root, text="Drop image files here or click to select a folder", width=50, height=10, bg="#3c3c3c", fg="white", relief="solid", bd=1)
drop_area.pack(padx=10, pady=10)
drop_area.bind("<Button-1>", lambda event: open_folder())

# dropdown box
format_var = tk.StringVar(value='png')
format_var.trace_add('write', on_format_change)
format_options = ['png', 'jpg', 'bmp', 'gif', 'webp', 'avif', 'jxl']
format_menu = ttk.OptionMenu(root, format_var, format_options[0], *format_options)
format_menu.pack(pady=10)

quality_frame = tk.Frame(root, bg="#2b2b2b")

# slider for quality
quality_var = tk.IntVar(value=100)
quality_slider = ttk.Scale(quality_frame, from_=10, to=100, orient='horizontal', variable=quality_var, length=200)
quality_slider.pack(side=tk.LEFT)
quality_slider.bind("<Motion>", on_quality_change)

# label for quality value
quality_value_label = ttk.Label(quality_frame, text=f"Quality: {quality_var.get()}", background='#2b2b2b', foreground='white')
quality_value_label.pack(side=tk.LEFT, padx=5)

# overwrite toggle
overwrite_var = tk.BooleanVar(value=True)
overwrite_checkbox = ttk.Checkbutton(root, text="Overwrite Source Files", variable=overwrite_var, style='TCheckbutton')
overwrite_checkbox.pack(pady=5)


on_format_change()

# log box
log_window = tk.Text(root, height=10, width=50, state=tk.DISABLED, bg="#2b2b2b", fg="white", relief="flat", highlightthickness=0)
log_window.pack(padx=10, pady=10)

drop_area.drop_target_register(DND_FILES)
drop_area.dnd_bind('<<Drop>>', drop)

root.mainloop()
