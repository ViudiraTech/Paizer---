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
    def __init__(self, master, nickname, server_ip_port):
        super().__init__(master)
        self.master = master
        self.nickname = nickname
        self.geometry("300x80")  # 增加窗口高度，确保所有组件都能显示
        self.resizable(width=False, height=False)
        self.server_ip_port = server_ip_port

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
                # 检查是否输入了端口号
                if ':' in self.server_ip_port:
                    server_ip, port_str = self.server_ip_port.split(':')
                    port = int(port_str)
                else:
                    server_ip = self.server_ip_port
                    port = 21156  # 默认端口号

                # 创建socket并连接到服务器
                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client.connect((server_ip, port))
                client.send(f"{self.nickname}".encode('utf-8'))
                connected = True
                self.receive_thread = threading.Thread(target=self.receive_message)
                self.receive_thread.start()
                print(f"成功登录到服务器 {server_ip}:{port}\n")
            except Exception as e:
                print(f"[!] 无法连接至服务器 {self.server_ip_port}: {e}")
                if client is not None:
                    client.close()
                connected = False
                messagebox.showerror("错误！", "无法连接到服务器，请检查服务器IP地址和端口号。")

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
                if client is not None:
                    client.close()
                connected = False
                break

def validate_input(nickname, server_ip_port):
    if not nickname.strip():
        messagebox.showwarning("警告！", "昵称不能为空。")
        return False
    try:
        # 尝试分割IP和端口，如果没有端口号，使用默认值
        server_ip, port_str = server_ip_port.rsplit(':', 1)
        port = int(port_str) if port_str.isdigit() else 21156  # 如果端口号是数字，则使用，否则使用默认端口
    except ValueError:
        # 如果没有分割出端口号，设置默认端口
        server_ip = server_ip_port
        port = 21156
    # 检查昵称和服务器IP地址是否有效
    if not server_ip.strip() or not port:
        messagebox.showwarning("警告！", "请输入有效的服务器IP地址和端口号。")
        return False
    return True

def on_connect(root, nickname, server_ip_port):
    if not validate_input(nickname, server_ip_port):
        return
    send_window = SendMessageWindow(root, nickname, server_ip_port)
    root.withdraw()

def main():
    root = tk.Tk()
    root.title("Paizer客户端")
    root.geometry("300x150")  # 主窗口大小
    root.resizable(width=False, height=False)

    nickname_label = tk.Label(root, text="键入您的昵称（支持中、英文）:")
    nickname_entry = tk.Entry(root)
    server_ip_port_label = tk.Label(root, text="键入服务器IP地址(可选端口，默认21156):")
    server_ip_port_entry = tk.Entry(root)

    nickname_label.pack()
    nickname_entry.pack()
    server_ip_port_label.pack()
    server_ip_port_entry.pack()

    connect_button = tk.Button(root, text="登录到服务器", command=lambda: on_connect(root, nickname_entry.get(), server_ip_port_entry.get()))
    connect_button.pack(pady=20)

    root.mainloop()

if __name__ == "__main__":
    main()