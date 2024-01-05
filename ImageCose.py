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
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif', '.cr2', '.arw', '.nef', '.rw2', '.raf')):
            image_path = os.path.join(folder_path, filename)

            if filename.lower().endswith(( '.cr2', '.arw', '.nef', '.rw2', '.raf')):
                with rawpy.imread(image_path) as raw:
                    rgb = raw.postprocess()
                img = Image.fromarray(rgb)
            else:
                img = Image.open(image_path)

            with open(image_path, 'rb') as f:
                exif_data = exifread.process_file(f)

            logo_folder = './Components/Logos'  # Logo文件夹路径
            iso = exif_data.get('EXIF ISOSpeedRatings')
            f = exif_data.get('EXIF FNumber')
            exposure_time = exif_data.get('EXIF ExposureTime')
            focal_length = exif_data.get('EXIF FocalLength')
            camera_make = exif_data.get('Image Make')  # 读取相机制造商信息
            camera_model = exif_data.get('Image Model')  # 从EXIF中获取相机型号
            date_time = exif_data.get('EXIF DateTimeOriginal')
            if date_time:
                formatted_date_time = date_time.values.replace(':', '/', 2)
            else:
                formatted_date_time = "未知时间"

            if f is not None:
                f_value = str(f)  # 将光圈值转换为字符串
                if '/' in f_value:
                    numerator, denominator = f_value.split('/')
                    f_number = float(numerator) / float(denominator)
                    f_formatted = f"{f_number:.1f}"  # 保留一位小数
                else:
                    f_formatted = f_value
            else:
                f_formatted = "未知"

            bar_height = int(img.height * 0.12) # Bar的高度
            feather = bar_height // 8  # 羽化调整
            gradient_bar = linear_gradient('#f7a8b8', '#99CCFF', img.width, bar_height, 180)
            mask = create_feathered_mask(gradient_bar.width, bar_height, feather)

            img_with_bar = Image.new('RGB', (img.width, img.height + gradient_bar.height - feather))
            img_with_bar.paste(img, (0, 0))
            img_with_bar.paste(gradient_bar, (0, img.height - feather), mask)

            draw = ImageDraw.Draw(img_with_bar)
            font_size = int(bar_height * 0.38)
            font = ImageFont.truetype("./Components/Fonts/AlibabaPuHuiTi-3-115-Black.ttf", font_size)  # 使用自定义字体

            text_line1 = f'ISO: {iso} | F/{f_formatted} | {exposure_time}S | {focal_length}MM'
            draw.text((10, img.height - feather + 5), text_line1, fill=(255,240,245), font=font)

            text_line2 = formatted_date_time
            draw.text((10, img.height + bar_height // 2 - feather + 5), text_line2, fill=(255,240,245), font=font)

            if camera_model:
                camera_model_text = camera_model.values if camera_model else '未知型号'
                text_width, text_height = draw.textsize(camera_model_text, font=font)

                # 计算在条形图中心放置文本的位置
                text_x = (img.width - text_width) // 2 + img.width * 0.2
                text_y = img.height + (bar_height - text_height) // 2 - feather

                draw.text((text_x, text_y), camera_model_text, fill=(212,242,231), font=font)

            if camera_make:
                logo_path = os.path.join(logo_folder, f'{camera_make.values[0]}.jpg')
                if os.path.exists(logo_path):
                    logo = Image.open(logo_path)

                    # 保持纵横比调整尺寸
                    aspect_ratio = logo.width / logo.height
                    new_height = int(bar_height * 0.85)
                    new_width = int(bar_height * 0.85 * aspect_ratio)
                    logo = logo.resize((new_width, new_height))

                    if logo.mode == 'RGBA':
                        # 分离出透明度蒙版
                        logo_mask = logo.split()[3]
                    else:
                        # 如果没有透明度通道，不使用蒙版
                        logo_mask = None

                    # 使用透明度蒙版（如果有的话）粘贴logo
                    img_with_bar.paste(logo, (
                        img.width - new_width - int(new_width * 0.2),
                        img.height + (bar_height - new_height) // 2 - feather), logo_mask)

            img_with_bar.show()


add_info_bar('./Image')
