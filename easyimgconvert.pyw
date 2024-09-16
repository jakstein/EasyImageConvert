import os
import tkinter as tk
from tkinter import Menu, ttk, filedialog
from tkinterdnd2 import DND_FILES, TkinterDnD
from PIL import Image, ExifTags
import pillow_avif
import pillow_jxl
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
    'ppm': True
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
    'ppm': 'PPM'
}
file_states = {}
# formats that support quality settings
quality_formats = ('jpg', 'jpeg', 'webp', 'avif', 'jxl')

# hold futures in a list
futures = []
lock = threading.Lock()

def convert_image(file_path, target_format, quality):
    target_format_pil = format_map[target_format.lower()]
    file_path_lower = file_path.lower()
    file_ext = os.path.splitext(file_path_lower)[1][1:]
    file_states[file_path] = 'processing'
    if file_ext == target_format.lower():
        file_states[file_path] = 'skipped'
        return f"Skipping {file_path}, already in {target_format.upper()} format."
    if not checkbox_vars.get(file_ext, False).get():
        file_states[file_path] = 'skipped'
        return f"Skipping {file_path}, format not selected in options."
    
    if file_path_lower.endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp', '.avif', '.jxl', '.ppm')):
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

            check_futures()
            if overwrite_var.get():
                # delete the original file if overwrite_var is True
                os.remove(file_path)
            return 
        except Exception as e:
            file_states[file_path] = 'error'
            check_futures()
            return 
    else:
        file_states[file_path] = 'notsupported'
        check_futures()
        return
    

def convert_and_replace(file_paths, target_format, quality):
    global futures
    with ThreadPoolExecutor(max_workers=worker_count_var.get()) as executor: # limit the number of workers
        futures = {executor.submit(convert_image, file_path, target_format, quality): file_path for file_path in file_paths}

def check_futures():
    global futures, file_states
    with lock:
        for future in futures.copy(): # iterate over a copy of the list
            if future.done() and future.result != 'skipped' or 'notsupported': 
                file_path = futures[future]
                try:
                    file_states[file_path] = 'completed'
                except Exception as e:
                    file_states[file_path] = 'error'
                futures.pop(future)
    log_states(file_states)    # update the log window

    if futures:
        root.after(100, check_futures)
    else:
        for file_path, state in file_states.items(): # bruteforce way to make everything completed, for some reason few items are left as processing despite being actually completed. errored items will still get logged properly
            if state == 'processing':
                file_states[file_path] = 'completed'
        log_states(file_states)  # final UI update once all tasks are done
        log_message("All tasks completed.")  # final log message

def process_directory(directory, target_format, quality):
    clear_log()
    if recursive_var.get():
        # recursive search for files
        for root_dir, _, files in os.walk(directory):
                file_paths = [os.path.join(root_dir, file) for file in files]
                for file_path in file_paths:
                    file_states[file_path] = 'todo'
                convert_and_replace(file_paths, target_format, quality)
    else:
        # non-recursive search for files
        file_paths = [os.path.join(directory, file) for file in os.listdir(directory)]
        convert_and_replace(file_paths, target_format, quality)

def drop(event): # drag and drop
    file_paths = root.tk.splitlist(event.data)
    target_format = format_var.get()
    quality = int(quality_var.get())
    threading.Thread(target=convert_and_replace, args=(file_paths, target_format, quality)).start()

def open_folder(): # open folder dialog
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        target_format = format_var.get()
        quality = int(quality_var.get())
        threading.Thread(target=process_directory, args=(folder_selected, target_format, quality)).start()
def log_states(states):
    clear_log()
    for file_path, state in states.items():
        if state == 'processing':
            log_message(f"{file_path}: processing")
        elif state == 'completed':
            log_message(f"{file_path}: completed")
        elif state == 'todo':
            log_message(f"{file_path}: to do")
        elif state == 'error':
            log_message(f"{file_path}: error")
        elif state == 'notsupported':
            log_message(f"{file_path}: not supported")
        elif state == 'skipped':
            log_message(f"{file_path}: skipped")
        else:
            log_message(f"{file_path}: unknown state")
    log_message("")
def log_message(message):
    log_window.config(state=tk.NORMAL)
    log_window.insert(tk.END, message + "\n")
    log_window.config(state=tk.DISABLED)
    log_window.yview(tk.END)
def clear_log():
    log_window.config(state=tk.NORMAL)
    log_window.delete('1.0', tk.END)
    log_window.config(state=tk.DISABLED)

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
format_options = ['png', 'jpg', 'bmp', 'gif', 'webp', 'avif', 'jxl', 'ppm']
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

# log box
log_window = tk.Text(root, height=20, width=100, state=tk.DISABLED, bg="#2b2b2b", fg="white", relief="flat", highlightthickness=0)
log_window.pack(padx=10, pady=10)

drop_area.drop_target_register(DND_FILES)
drop_area.dnd_bind('<<Drop>>', drop)

root.mainloop()
