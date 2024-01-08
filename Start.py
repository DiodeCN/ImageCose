import tkinter as tk
from subprocess import Popen, PIPE, STDOUT
import threading
import os


def run_imagecose_script():
    def read_output(process, text_widget):
        while True:
            line = process.stdout.readline()
            if not line:
                break
            decoded_line = line.decode('utf-8', errors='replace')  # 解码为 utf-8，替换任何无法解码的字符
            text_widget.insert(tk.END, decoded_line)
            text_widget.see(tk.END)

    script_path = './ImageCose.py'  # 确保这是正确的路径
    process = Popen(['python', script_path], stdout=PIPE, stderr=STDOUT)

    # 在新线程中读取输出
    threading.Thread(target=read_output, args=(process, output_text), daemon=True).start()


# 创建基本窗口
root = tk.Tk()
root.title("启动 ImageCose")

# 创建一个文本框，用于显示输出
output_text = tk.Text(root, height=10, width=50)
output_text.pack(pady=20)

# 创建一个按钮，点击时运行 ImageCose.py 脚本
start_button = tk.Button(root, text='启动 ImageCose', command=run_imagecose_script)
start_button.pack(pady=20)

# 运行 Tkinter 事件循环
root.mainloop()
