# By ViudiraTech
# GPL-2.0 LICENSE

import socket
import threading
import tkinter as tk
from tkinter import messagebox

print('Paizer客户端')

# 全局变量用于存储socket客户端对象和连接状态
client = None
connected = False

class SendMessageWindow(tk.Toplevel):
    def __init__(self, master, nickname, server_ip):
        super().__init__(master)
        self.master = master
        self.nickname = nickname
        self.geometry("300x80")  # 增加窗口高度，确保所有组件都能显示
        self.resizable(width=False, height=False)
        self.server_ip = server_ip

        # 输入框
        self.message_entry = tk.Entry(self, width=50)
        self.message_entry.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        self.bind_keys()

        # 发送按钮
        self.send_button = tk.Button(self, text="发送", command=lambda: self.send_message(self.message_entry.get()), width=8)
        self.send_button.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 10), anchor=tk.CENTER)

        # 如果尚未连接，尝试连接到服务器
        if not connected:
            self.create_connection()

    def bind_keys(self):
        # 绑定键盘事件 <Return> 到 send_message 方法
        self.message_entry.bind('<Return>', self.send_message)

    def create_connection(self):
        global client, connected
        if not connected:
            try:
                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client.connect((self.server_ip, 21156))
                client.send(f"{self.nickname}".encode('utf-8'))
                connected = True
                self.receive_thread = threading.Thread(target=self.receive_message)
                self.receive_thread.start()
                print("成功登录到服务器\n")
            except Exception as e:
                print(f"[!] 无法连接至服务器 {self.server_ip}: {e}")
                client.close()
                connected = False
                messagebox.showerror("错误！", "无法连接到服务器，请检查服务器IP地址。")
                # 不再创建SendMessageWindow实例

    def send_message(self, event=None):
        # 获取输入框中的文本
        message = self.message_entry.get()
        # 检查是否有消息文本
        if message:
            # 发送消息
            global client
            client.send((self.nickname + ": " + message).encode('utf-8'))
            # 清空输入框
            self.message_entry.delete(0, tk.END)

    def receive_message(self):
        while True:
            try:
                message = client.recv(1024).decode('utf-8')
                print(message)
            except Exception as e:
                print(f"[!] 接收消息时发生错误: {e}")
                client.close()
                connected = False
                break

def validate_input(nickname, server_ip):
    if not nickname.strip():
        messagebox.showwarning("警告！", "昵称不能为空。")
        return False
    if not server_ip.strip():
        messagebox.showwarning("警告！", "服务器 IP 地址不能为空。")
        return False
    return True

def on_connect(root, nickname, server_ip):
    if not validate_input(nickname, server_ip):
        return
    send_window = SendMessageWindow(root, nickname, server_ip)
    root.withdraw()

def main():
    root = tk.Tk()
    root.title("Paizer客户端")
    root.geometry("300x150")  # 主窗口大小
    root.resizable(width=False, height=False)

    nickname_label = tk.Label(root, text="键入您的昵称:")
    nickname_entry = tk.Entry(root)
    server_ip_label = tk.Label(root, text="键入服务器的IP地址:")
    server_ip_entry = tk.Entry(root)

    nickname_label.pack()
    nickname_entry.pack()
    server_ip_label.pack()
    server_ip_entry.pack()

    connect_button = tk.Button(root, text="登录到服务器", command=lambda: on_connect(root, nickname_entry.get(), server_ip_entry.get()))
    connect_button.pack(pady=20)

    root.mainloop()

if __name__ == "__main__":
    main()