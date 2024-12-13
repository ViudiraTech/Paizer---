# By ViudiraTech
# MIT LICENSE ¯\_(ツ)_/¯

# 导入必要的库
import socket  # 用于创建网络通信的socket
import threading  # 用于创建和管理线程
import tkinter as tk  # 用于创建GUI
from tkinter import messagebox  # 用于显示消息框
import ctypes  # 用于调用Windows API函数
import shelve  # 用于创建简单的持久化数据库
import pickle  # 用于序列化和反序列化Python对象
import os  # 用于操作系统功能，如文件路径操作
import appdirs  # 用于获取应用程序数据目录的库
import time  # 用于时间相关的功能

# 全局变量用于存储socket客户端对象和连接状态
client = None
connected = False
login_window = None

# 登录界面的GUI类
class LoginGUI:
    def __init__(self, master):
        # 初始化方法，设置窗口属性和控件
        self.master = master  # 存储传入的Tk实例
        self.master.title("Paizer客户端 - 登录")  # 设置窗口标题
        self.master.geometry("280x150")  # 设置登录窗口大小
        self.master.resizable(width=False, height=False)  # 禁止调整窗口大小

        # 昵称标签和输入框
        self.nickname_label = tk.Label(self.master, text="用户昵称(支持中英文、数字符号):")
        self.nickname_label.pack()
        self.nickname_entry = tk.Entry(self.master, width=20)
        self.nickname_entry.pack()

        # 服务器IP地址标签和输入框
        self.server_ip_port_label = tk.Label(self.master, text="服务器IP地址(端口留空为21156):")
        self.server_ip_port_label.pack()
        self.server_ip_port_entry = tk.Entry(self.master, width=20)
        self.server_ip_port_entry.pack()

        # 绑定回车键事件到 login_on_enter 方法
        self.master.bind('<KeyPress-Return>', self.login_on_enter)

        # 登录按钮
        self.login_button = tk.Button(self.master, text="登录服务器", command=self.login, width=15)
        self.login_button.pack(pady=10)

        # 加载之前保存的输入数据
        self.nickname, self.server_ip_port = load_input_data()
        self.nickname_entry.insert(0, self.nickname)
        self.server_ip_port_entry.insert(0, self.server_ip_port)

    def login_on_enter(self, event):
        # 调用登录方法，忽略事件对象
        self.login()

    def login(self):
        # 获取输入的昵称和服务器IP端口
        nickname = self.nickname_entry.get()
        server_ip_port = self.server_ip_port_entry.get()

        # 保存输入数据
        save_input_data(nickname, server_ip_port)

        # 验证输入
        if validate_input(nickname, server_ip_port):
            # 如果验证通过，调用on_connect函数
            global login_window
            login_window = self.master  # 确保全局变量引用当前的登录窗口
            on_connect(nickname, server_ip_port, self.master)

            # 隐藏登录窗口
            self.master.withdraw()

# 客户端GUI的主类
class PaizerClientGUI:
    def __init__(self, master, nickname, server_ip_port):
        # 初始化方法，设置窗口属性、控件和事件处理
        self.master = master
        self.master.title(f"Paizer客户端 - {server_ip_port} - {nickname}")  # 设置窗口标题
        self.master.geometry("570x470")  # 设置GUI窗口大小
        self.master.resizable(width=False, height=False)

        self.nickname = nickname
        self.server_ip_port = server_ip_port

        # 创建消息显示区域
        self.message_text = tk.Text(self.master, height=15, width=60, font=('微软雅黑', 13))
        self.message_text.pack(expand=True, fill='both')

        # 创建滚动条
        self.scrollbar = tk.Scrollbar(self.master, command=self.message_text.yview)
        self.scrollbar.pack(side='right', fill='y')

        # 绑定滚动条和文本框
        self.message_text.config(yscrollcommand=self.scrollbar.set)

        # 创建底部框架，用于放置输入框和发送按钮
        bottom_frame = tk.Frame(self.master, bd=2, relief=tk.SUNKEN)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        # 输入框
        self.message_entry = tk.Entry(bottom_frame, width=60)
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, padx=(10, 5), pady=(10, 10), expand=True)

        # 绑定回车键事件
        self.message_entry.bind('<Return>', self.send_message_on_enter)

        # 发送按钮
        self.send_button = tk.Button(bottom_frame, text="发送", command=self.send_message, width=15)
        self.send_button.pack(side=tk.LEFT, padx=(5, 10), pady=(10, 10))

        # 尝试连接到服务器
        self.create_connection()

        self.master.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        # 询问用户是否确实想要退出
        choice = messagebox.askyesno("退出确认", "您确定要退出Paizer客户端吗？")
        if choice:  # 用户点击“是”
            try:
                # 发送关闭请求到服务端
                if client is not None and connected:
                    client.send("CLOSE_REQUEST".encode('utf-8'))
                time.sleep(0.5)  # 等待0.5秒，确保消息发送完成
            except Exception as e:
                print(f"[!] 发送关闭请求时发生错误: {e}")
            finally:
                # 尝试安全地关闭socket连接
                if client is not None:
                    client.close()
                ctypes.windll.kernel32.ExitProcess(0)  # 强制结束程序

    # 新的方法，当按下回车键时调用
    def send_message_on_enter(self, event):
        self.send_message()

    def create_connection(self):
        global client, connected
        if not connected:
            try:
                # 解析服务器IP和端口
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
                self.log_message("Paizer客户端")
                self.log_message(f"成功登录至服务器 {server_ip}:{port}\n")
            except Exception as e:
                self.log_message(f"[!] 无法连接至服务器 {self.server_ip_port}: {e}")
                if client is not None:
                    client.close()
                connected = False

    def send_message(self):
        # 发送消息到服务器的方法
        message = self.message_entry.get()
        if message:
            # 格式化消息为 "用户名: 消息内容"
            formatted_message = f"{self.nickname}: {message}"
            client.send(formatted_message.encode('utf-8'))
            self.message_entry.delete(0, tk.END)

    def receive_message(self):
        # 接收来自服务器的消息的方法
        while True:
            try:
                message = client.recv(1024).decode('utf-8')
                # 假设消息格式为 "昵称: 消息内容"，且不包含发送者的IP地址
                self.log_message(message)
            except Exception as e:
                self.log_message(f"[!] 接收消息时发生错误: {e}")
                if client is not None:
                    client.close()
                connected = False
                break

    def log_message(self, message):
        # 将消息添加到文本框中的方法
        self.message_text.config(state='normal')  # 允许编辑文本框
        self.message_text.insert(tk.END, message + '\n')
        self.message_text.config(state='disabled')  # 禁止编辑文本框
        self.message_text.yview(tk.END)  # 自动滚动到最新消息

# 保存用户输入数据到本地的方法
def save_input_data(nickname, server_ip_port):
    # 获取应用程序数据目录
    data_dir = appdirs.user_data_dir('Paizer', 'ViudiraTech')
    # 创建配置文件的完整路径
    config_file = os.path.join(data_dir, 'user_data.dat')
    try:
        with shelve.open(config_file, 'c') as db:  # 使用'c'模式创建新数据库
            db['nickname'] = nickname
            db['server_ip_port'] = server_ip_port
    except Exception as e:
        print(f"[!] 保存输入数据时发生错误: {e}")

# 从本地加载用户输入数据的方法
def load_input_data():
    # 获取应用程序数据目录
    data_dir = appdirs.user_data_dir('Paizer', 'ViudiraTech')
    # 创建配置文件的完整路径
    config_file = os.path.join(data_dir, 'user_data.dat')

    # 确保数据目录存在
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    # 尝试加载或创建数据
    try:
        with shelve.open(config_file, 'r') as db:  # 使用'r'模式打开现有数据库
            nickname = db.get('nickname', '')  # 获取保存的昵称，如果不存在则返回空字符串
            server_ip_port = db.get('server_ip_port', '')  # 获取保存的服务器IP和端口，如果不存在则返回空字符串
            return nickname, server_ip_port
    except Exception as e:
        print(f"[!] 加载输入数据时发生错误: {e}")
        return '', ''  # 如果发生错误，返回默认值

# 验证用户输入是否有效的方法
def validate_input(nickname, server_ip_port, parent=None):
    # 检查昵称是否为空
    if not nickname.strip():
        messagebox.showwarning("警告！", "昵称不能为空。", parent=parent)
        return False
    # 检查是否包含端口号
    try:
        # 如果包含冒号，则分割IP和端口
        if ':' in server_ip_port:
            server_ip, port_str = server_ip_port.split(':')
            port = int(port_str)
        else:
            # 否则，使用默认端口号
            server_ip = server_ip_port
            port = 21156
    except ValueError:
        messagebox.showwarning("警告！", "请输入有效的服务器IP地址和端口号。", parent=parent)
        return False
    # 检查IP地址是否有效
    if not server_ip.strip():
        messagebox.showwarning("警告！", "请输入有效的服务器IP地址。", parent=parent)
        return False
    return True

# 当连接到服务器后创建新的GUI窗口的方法
def on_connect(nickname, server_ip_port, login_root):
    # 隐藏登录窗口
    login_root.withdraw()

    # 创建新的GUI窗口实例
    root = tk.Tk()
    app = PaizerClientGUI(root, nickname, server_ip_port)

    # 启动新的GUI窗口的主循环
    root.mainloop()

# 主函数，程序入口点
def main():
    # 创建登录窗口
    login_root = tk.Tk()
    global login_window
    login_window = login_root
    login_app = LoginGUI(login_root)
    login_root.mainloop()

# 程序运行时的入口点
if __name__ == "__main__":
    main()