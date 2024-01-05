from PIL import Image, ImageDraw, ImageFont
import exifread
import os
import rawpy
import numpy as np


def linear_gradient(start_color, end_color, width, height, angle):
    """ 创建一个线性渐变的背景 """
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


def add_info_bar(folder_path):
    # 遍历文件夹中的所有文件
    for filename in os.listdir(folder_path):
        # 检查文件是否为图片
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif', '.cr2', '.arw')):
            image_path = os.path.join(folder_path, filename)

            # 检查是否为原始格式
            if filename.lower().endswith(('.cr2', '.arw')):
                # 使用 rawpy 处理原始格式
                with rawpy.imread(image_path) as raw:
                    rgb = raw.postprocess()
                img = Image.fromarray(rgb)
            else:
                # 打开非原始格式的图片
                img = Image.open(image_path)

            # 获取图片的 EXIF 数据
            with open(image_path, 'rb') as f:
                exif_data = exifread.process_file(f)

            # 提取所需的 EXIF 信息
            iso = exif_data.get('EXIF ISOSpeedRatings')
            f = exif_data.get('EXIF FNumber')
            exposure_time = exif_data.get('EXIF ExposureTime')
            focal_length = exif_data.get('EXIF FocalLength')
            date_time = exif_data.get('EXIF DateTimeOriginal')

            bar_height = int(img.height * 0.1)
            gradient_bar = linear_gradient('#f7a8b8', '#99CCFF', img.width, bar_height, 0)
            img_with_bar = Image.new('RGB', (img.width, img.height + gradient_bar.height))
            img_with_bar.paste(img, (0, 0))
            img_with_bar.paste(gradient_bar, (0, img.height))

            draw = ImageDraw.Draw(img_with_bar)

            # 根据横条的高度设置字体大小
            font_size = int(bar_height * 0.36)  # 根据需要调整这个比例
            font = ImageFont.truetype(".\Components\Fonts\AlibabaPuHuiTi-3-115-Black.ttf", font_size)  # 使用自定义字体

            # 绘制第一行文本
            text_line1 = f'ISO: {iso}|F/{f}|{exposure_time}S|{focal_length}MM'
            draw.text((10, img.height + 5), text_line1, fill='white', font=font)

            # 绘制第二行文本
            text_line2 = f'日期: {date_time}'
            draw.text((10, img.height + bar_height // 2 + 5), text_line2, fill='white', font=font)

            # 保存或显示图片
            img_with_bar.show()


# 使用文件夹路径调用函数
add_info_bar('.\Image')
