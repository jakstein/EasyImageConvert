# EasyImageConvert
A simple and minimalist image converter GUI written in Python, written out of dislike for bloat other converters offer, while still keeping a simple GUI. Also to practice coding skills.

Supports drag and drop operations, as well as just clicking the upload box and selecting folder with images.

The images will be scanned in the main folder and subfolders. (Planning to add a toggle to disable that)

The script also overwrites the images upon successful conversion. (Also have to add a toggle for that)

Supported formats: PNG, JPEG, JPG, BMP, GIF, WEBP, AVIF, JXL.
For formats that support it, it also accepts quality setting.

Usage:

Run the script using Python: ```python easyimgconvert.pyw```

Required packages: 
```python
pip install tkinterdnd2 Pillow pillow_avif pillow_jxl
```
[![image.png](https://i.postimg.cc/SK0zy32x/image.png)](https://postimg.cc/SnrKdZfB)
