from PIL import Image, ImageDraw, ImageFont, ImageFilter
import exifread
import os
import rawpy


def linear_gradient(start_color, end_color, width, height, angle):
    """Create a linear gradient background"""
    base = Image.new('RGB', (width, height), start_color)
    top = Image.new('RGB', (width, height), end_color)

    mask = Image.new('L', (width, height))
    mask_data = []
    for y in range(height):
        for x in range(width):
            mask_data.append(int(255 * (x / width)))
    mask.putdata(mask_data)

    base.paste(top, (0, 0), mask)
    return base.rotate(angle)


def create_feathered_mask(width, height, feather):
    """Create a feathered mask to blend the image and the bar smoothly"""
    mask = Image.new('L', (width, height), 0)  # Initialize with 0 (transparent)
    for i in range(feather):
        opacity = int(255 * (i / feather))
        for j in range(width):
            mask.putpixel((j, i), opacity)
    for i in range(feather, height):
        for j in range(width):
            mask.putpixel((j, i), 255)  # Fully opaque for the rest of the mask
    return mask.filter(ImageFilter.GaussianBlur(radius=feather // 2))


def add_info_bar(folder_path):
    # Iterate over all the files in the folder
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif', '.cr2', '.arw')):
            image_path = os.path.join(folder_path, filename)

            if filename.lower().endswith(('.cr2', '.arw')):
                with rawpy.imread(image_path) as raw:
                    rgb = raw.postprocess()
                img = Image.fromarray(rgb)
            else:
                img = Image.open(image_path)

            with open(image_path, 'rb') as f:
                exif_data = exifread.process_file(f)

            iso = exif_data.get('EXIF ISOSpeedRatings')
            f = exif_data.get('EXIF FNumber')
            exposure_time = exif_data.get('EXIF ExposureTime')
            focal_length = exif_data.get('EXIF FocalLength')
            date_time = exif_data.get('EXIF DateTimeOriginal')

            bar_height = int(img.height * 0.1)
            feather = bar_height // 6  # 羽化调整
            gradient_bar = linear_gradient('#f7a8b8', '#99CCFF', img.width, bar_height, 0)
            mask = create_feathered_mask(gradient_bar.width, bar_height, feather)

            img_with_bar = Image.new('RGB', (img.width, img.height + gradient_bar.height - feather))
            img_with_bar.paste(img, (0, 0))
            img_with_bar.paste(gradient_bar, (0, img.height - feather), mask)

            draw = ImageDraw.Draw(img_with_bar)
            font_size = int(bar_height * 0.36)
            font = ImageFont.truetype(".\Components\Fonts\AlibabaPuHuiTi-3-115-Black.ttf", font_size)  # 使用自定义字体

            text_line1 = f'ISO: {iso} | F/{f} | {exposure_time}S | {focal_length}MM'
            draw.text((10, img.height - feather + 5), text_line1, fill='white', font=font)

            text_line2 = f'日期: {date_time}'
            draw.text((10, img.height + bar_height // 2 - feather + 5), text_line2, fill='white', font=font)

            img_with_bar.show()


add_info_bar('./Image')
