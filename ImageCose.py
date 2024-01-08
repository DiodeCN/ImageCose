from PIL import Image, ImageDraw, ImageFont, ImageFilter
import exifread
import os
import sys
import time
import rawpy
import threading

brand_names = ['Canon', 'Sony', 'Nikon', 'Fujifilm', 'Panasonic', 'Olympus', 'Leica', 'Pentax', 'Hasselblad', 'Ricoh']


def remove_brand_names(model_text, brand_names):
    """Remove brand names from the model text."""
    for brand in brand_names:
        model_text = model_text.replace(brand, '')
    return model_text.strip()  # 去除可能出现的前后空格



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

def process_image(image_path):
    output_folder = './Output'
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    filename = os.path.basename(image_path)

    # 处理 RAW 文件
    if filename.lower().endswith(('.cr2', '.arw', '.nef', '.rw2', '.raf')):
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
    artist = exif_data.get('Image Copyright')
    print(artist)

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

    is_portrait = img.height > img.width

    bar_height = int(img.height * 0.123)  # Bar的高度
    feather = bar_height // 25  # 羽化调整
    gradient_bar = linear_gradient('#FEEFF5', '#F0F4FF', img.width, bar_height, 180)
    mask = create_feathered_mask(gradient_bar.width, bar_height, feather)

    img_with_bar = Image.new('RGB', (img.width, img.height + gradient_bar.height - feather))
    img_with_bar.paste(img, (0, 0))
    img_with_bar.paste(gradient_bar, (0, img.height - feather), mask)

    draw = ImageDraw.Draw(img_with_bar)
    font_size = int(bar_height * 0.38)
    fontHeavy = ImageFont.truetype("./Components/Fonts/AlibabaPuHuiTi-3-95-ExtraBold.ttf", font_size)  # 使用自定义字体
    fontBlack = ImageFont.truetype("./Components/Fonts/AlibabaPuHuiTi-3-115-Black.ttf",
                                   int(font_size * 1.25))  # 使用自定义字体
    signfont = ImageFont.truetype("./Components/Fonts/Meticulous-Regular.ttf", int(font_size * 1.65))  # 使用自定义字体
    timefont = ImageFont.truetype("./Components/Fonts/Ubuntu-M.ttf", font_size)  # 使用自定义字体

    if not is_portrait:
        text_line1 = f'ISO-{iso} | F/{f_formatted} | {exposure_time}S | {focal_length}MM'
        draw.text((10, img.height - feather + 5), text_line1, fill='#032582', font=fontHeavy)

        artist_text = (' -' + artist.values[0] if artist else ' -ElmCose')
        date_text_x = 10
        date_text_y = img.height + bar_height // 2 - feather + 5

        draw.text((date_text_x, date_text_y), formatted_date_time, fill='#032582', font=timefont)
        date_text_width, _ = draw.textsize(formatted_date_time, font=timefont)
        artist_text_x = date_text_x + date_text_width
        draw.text((artist_text_x, date_text_y * 0.98), artist_text, fill='#800000', font=signfont)

    if camera_make:
        logo_path = os.path.join(logo_folder, f'{camera_make.values[0]}.jpg')
        if os.path.exists(logo_path):
            logo = Image.open(logo_path)
            aspect_ratio = logo.width / logo.height
            new_height = int(bar_height * 0.8)
            new_width = int(bar_height * 0.78 * aspect_ratio)

            logo = logo.resize((new_width, new_height))
            logo_x = img.width - new_width - int(new_width * 0.2)
            logo_y = img.height + (bar_height - new_height) // 2 - feather + new_height // 16  # 煞费苦心的修改Y对齐

            if logo.mode == 'RGBA':
                # 分离出透明度蒙版
                logo_mask = logo.split()[3]
            else:
                # 如果没有透明度通道，不使用蒙版
                logo_mask = None

            # 使用透明度蒙版（如果有的话）粘贴logo
            img_with_bar.paste(logo, (logo_x, logo_y), logo_mask)

            if camera_model:
                camera_model_text = camera_model.values if camera_model else '未知型号'
                # 在展示之前去除商标名
                camera_model_text = remove_brand_names(camera_model_text, brand_names)
                text_width, text_height = draw.textsize(camera_model_text, font=fontBlack)

                if is_portrait:
                    text_x = logo_x * 0.92 - text_width
                else:
                    text_x = logo_x * 0.97 - text_width

                text_y = img.height * 0.99 + (bar_height - text_height) // 2 - feather
                draw.text((text_x, text_y), f'{camera_model_text} | ', fill='#00520A', font=fontBlack)

                output_filename = os.path.splitext(filename)[0] + '.jpg'
                output_path = os.path.join(output_folder, output_filename)

                # 保存处理后的图像为 JPEG 格式
                img_with_bar.save(output_path, 'JPEG')
                img_with_bar.show(output_path)

                # 打印处理完成的消息
                print(f'处理完成：{output_filename}')


def add_info_bar(folder_path):
    start_time = time.time()  # 开始计时

    output_folder = './Output'
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    threads = []
    max_threads = 32   # 您可以根据您的系统资源调整这个数字

    for filename in os.listdir(folder_path):
        if filename.lower().endswith(
                ('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif', '.cr2', '.arw', '.nef', '.rw2', '.raf')):
            image_path = os.path.join(folder_path, filename)
            # 创建一个线程来处理图像
            thread = threading.Thread(target=process_image, args=(image_path,))
            threads.append(thread)
            thread.start()

            # 如果达到了最大线程数，等待一些线程完成
            while len(threads) >= max_threads:
                for t in threads:
                    if not t.is_alive():
                        threads.remove(t)

    # 等待所有线程完成
    for t in threads:
        t.join()

    end_time = time.time()  # 结束计时
    total_time = end_time - start_time

    print(f"所有图像处理完成。用时 {total_time:.2f} 秒。")

# 调用函数处理整个文件夹
print(sys.executable)
print(sys.version)
add_info_bar('./Image')
