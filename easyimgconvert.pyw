import os
import tkinter as tk
from tkinter import Menu, ttk, filedialog
from tkinterdnd2 import DND_FILES, TkinterDnD
from PIL import Image, ExifTags
import pillow_avif
import pillow_jxl
import pillow_heif
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# define supported image formats
inputformats = {
    'png': True,
    'jpg': True,
    'jpeg': True,
    'bmp': True,
    'gif': True,
    'webp': True,
    'avif': True,
    'jxl': True,
    'ppm': True,
    'heic': True
}
# map format options to PIL format strings
format_map = {
    'png': 'PNG',
    'jpg': 'JPEG',
    'jpeg': 'JPEG',
    'bmp': 'BMP',
    'gif': 'GIF',
    'webp': 'WEBP',
    'avif': 'AVIF',
    'jxl': 'JXL',
    'ppm': 'PPM',
    'heic': 'HEIC'
}
# formats that support quality settings
quality_formats = ('jpg', 'jpeg', 'webp', 'avif', 'jxl', 'heic')

# hold futures in a list
futures = []
lock = threading.Lock()

def convert_image(file_path, target_format, quality):
    target_format_pil = format_map[target_format.lower()]
    file_path_lower = file_path.lower()
    file_ext = os.path.splitext(file_path_lower)[1][1:]
    if file_ext == target_format.lower():
        return
    if not checkbox_vars.get(file_ext, False).get():
        return
    
    if file_path_lower.endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp', '.avif', '.jxl', '.ppm', '.heic')):
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
            
            # save the image in the chosen format with quality and EXIF data if available
            save_args = {}
            if target_format.lower() in quality_formats:
                save_args['quality'] = quality
            if exif_data:
                save_args['exif'] = exif_data
            img.save(new_file_path, target_format_pil, **save_args)

            if overwrite_var.get():
                # delete the original file if overwrite_var is True
                os.remove(file_path)
            return 
        except Exception as e:
            return 
    else:
        return
    
def convert_and_replace(file_paths, target_format, quality):
    global futures
    with ThreadPoolExecutor(max_workers=worker_count_var.get()) as executor: # limit the number of workers
        futures = {executor.submit(convert_image, file_path, target_format, quality): file_path for file_path in file_paths}
        check_futures()

def check_futures():
    global futures
    with lock:
        all_done = all(f.done() for f in futures)
        if all_done:
            futures.clear()

    if not futures:
        working_var.set(False)
    else:
        root.after(3000, check_futures)

def process_directory(directory, target_format, quality):
    working_var.set(True)
    if recursive_var.get():
        # recursive search for files
        for root_dir, _, files in os.walk(directory):
                file_paths = [os.path.join(root_dir, file) for file in files]
                convert_and_replace(file_paths, target_format, quality)
    else:
        # non-recursive search for files
        file_paths = [os.path.join(directory, file) for file in os.listdir(directory)]
        convert_and_replace(file_paths, target_format, quality)

def drop(event): # drag and drop
    working_var.set(True)
    file_paths = root.tk.splitlist(event.data)
    target_format = format_var.get()
    quality = int(quality_var.get())
    threading.Thread(target=convert_and_replace, args=(file_paths, target_format, quality)).start()

def open_folder(): # open folder dialog
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        working_var.set(True)
        target_format = format_var.get()
        quality = int(quality_var.get())
        threading.Thread(target=process_directory, args=(folder_selected, target_format, quality)).start()

def on_format_change(*args):
    selected_format = format_var.get().lower()
    if selected_format in quality_formats:
        quality_frame.pack(side=tk.TOP, pady=5)
    else:
        quality_frame.pack_forget()

def on_quality_change(event):
    quality_value_label.config(text=f"Quality: {int(quality_var.get())}")

# create the main application window and apply fancy colors
root = TkinterDnD.Tk()
root.title("Image Converter")
root.geometry("400x600")
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
style.configure('TCheckbutton', background='#2b2b2b', foreground='white', font=('Helvetica', 10))
style.map('TCheckbutton',
          background=[('active', '#2b2b2b'), ('!active', '#2b2b2b')],
          indicatorcolor=[('selected', '#007acc'), ('!selected', '#555555')],
          foreground=[('active', 'white'), ('!active', 'white')])
style.configure('TText', background='#2b2b2b', foreground='white')

root.configure(bg='#2b2b2b')

drop_area = tk.Label(root, text="Drop image files here or click to select a folder", width=50, height=10, bg="#3c3c3c", fg="white", relief="solid", bd=1)
drop_area.pack(padx=10, pady=10)
drop_area.bind("<Button-1>", lambda event: open_folder())

# menu for recrursive/overwrite options
recursive_var = tk.BooleanVar(value=True)
overwrite_var = tk.BooleanVar(value=True)
menu_bar = Menu(root)
root.config(menu=menu_bar)
file_menu = Menu(menu_bar, tearoff=0)
format_menu = Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Options", menu=file_menu)
file_menu.add_checkbutton(label="Recursive", variable=recursive_var)
file_menu.add_checkbutton(label="Overwrite", variable=overwrite_var)
file_menu.add_separator()
file_menu.add_command(label="Exit", command=root.quit)
menu_bar.add_cascade(label="Input formats", menu=format_menu)
# create a checkbutton for each input format
checkbox_vars = {}
for format_name, is_checked in inputformats.items():
    # import inputformats values and set them as the initial state of the checkbutton
    var = tk.BooleanVar(value=is_checked)
    checkbox_vars[format_name] = var  # store the state of the checkbutton for next loop with the name of format as key
    format_menu.add_checkbutton(label=format_name.upper(), variable=var)

# menu for futures worker count
worker_count_var = tk.IntVar(value=2)
worker_count_menu = Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Worker count", menu=worker_count_menu)
for i in range(1, 9):
    worker_count_menu.add_radiobutton(label=str(i), variable=worker_count_var, value=i)

# dropdown box
format_var = tk.StringVar(value='png')
format_var.trace_add('write', on_format_change)
format_options = ['png', 'jpg', 'bmp', 'gif', 'webp', 'avif', 'jxl', 'ppm', 'heic']
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

on_format_change()

working_var = tk.BooleanVar(value=False)
working_check = ttk.Checkbutton(root, text="Working", variable=working_var, state=tk.DISABLED)
working_check.pack(pady=10)

drop_area.drop_target_register(DND_FILES)
drop_area.dnd_bind('<<Drop>>', drop)

root.mainloop()
