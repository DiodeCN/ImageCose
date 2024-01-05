from PIL import Image, ImageDraw, ImageFont
import exifread
import os
import rawpy
import numpy as np


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
            shutter_speed = exif_data.get('EXIF ShutterSpeedValue')
            aperture = exif_data.get('EXIF ApertureValue')
            date_time = exif_data.get('EXIF DateTimeOriginal')

            # 创建一个带信息的白色横条
            bar_height = 50
            img_with_bar = Image.new('RGB', (img.width, img.height + bar_height), 'white')
            img_with_bar.paste(img, (0, 0))

            draw = ImageDraw.Draw(img_with_bar)
            font = ImageFont.load_default()
            text = f'ISO: {iso}, Shutter Speed: {shutter_speed}, Aperture: {aperture}, Date: {date_time}'
            draw.text((10, img.height + 10), text, fill='black', font=font)

            # 保存或显示图片
            img_with_bar.show()


# 使用文件夹路径调用函数
add_info_bar('D:\ImageCose\Image')
