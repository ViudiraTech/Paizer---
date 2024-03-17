# By ViudiraTech
# GPL-2.0 LICENSE ¯\_(ツ)_/¯

# 导入必要的库
import socket  # 用于网络通信
import threading  # 用于创建和管理线程
from datetime import datetime  # 用于获取当前时间

# 获取本机的IPv4地址
def get_local_ipv4():
    interfaces = socket.getaddrinfo(socket.gethostname(), None)  # 获取主机名对应的IP地址信息
    for interface in interfaces:
        address = interface[4][0]  # 获取IP地址
        if address.startswith('192.168') or address.startswith('10.') or address.startswith('172.'):
            return address  # 如果地址是私有地址，则返回
    return '无法获取IPv4内网地址'  # 如果无法获取有效的内网地址，则返回错误信息

# 获取服务端监听端口
def get_server_port():
    while True:
        input_port = input("设置服务端监听端口（留空为21156）：")  # 提示用户输入端口号
        if not input_port:  # 如果用户没有输入，则使用默认端口21156
            port = 21156
        else:
            try:
                port = int(input_port)  # 尝试将输入转换为整数
                if 0 < port < 65536:  # 检查端口号是否在有效范围内
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as test_socket:
                        try:
                            test_socket.bind(('localhost', port))  # 尝试绑定端口
                        except PermissionError:  # 如果端口已被占用或不允许访问
                            print(f"端口 {port} 已被占用或不允许访问。请重新输入端口号。")
                            continue
                else:
                    print("端口号无效，请输入1到65535之间的数字。")
            except ValueError:  # 如果输入不是有效的整数
                print("请输入一个有效的端口号。")
        return port  # 返回用户输入的有效端口号

# 初始化服务端
print('Paizer服务端\n')
server_port = get_server_port()  # 获取并设置服务端监听端口
print()
print(f"[*] 当前服务端监听端口: {server_port}")  # 打印服务端监听的端口

local_ipv4 = get_local_ipv4()  # 获取本机内网IP地址
print(f"[*] 当前服务器内网地址: {local_ipv4}")  # 打印内网IP地址

# 创建socket对象并绑定端口，开始监听
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('0.0.0.0', server_port))
server.listen(5)
server_ip, server_port = server.getsockname()  # 获取绑定的IP地址和端口号
print(f"[*] 正在监听 {server_ip}:{server_port}\n")  # 打印服务器监听的信息

clients = []  # 存储所有客户端的列表

# 处理客户端连接的函数
def handle_client(client_socket, client_address, broadcast):
    # 接收客户端的昵称
    client_nickname = client_socket.recv(1024).decode('utf-8').strip(': ')
    current_time = datetime.now().strftime("%H:%M:%S")
    print(f"\n[*] [{current_time}] {client_nickname} 加入了服务器\n")  # 打印客户端加入信息
    broadcast(client_socket, f"\n[*] [{current_time}] {client_nickname} 加入了服务器\n")  # 广播客户端加入信息
    
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')  # 接收客户端发送的消息
            if message == "CLOSE_REQUEST":  # 如果消息是关闭请求
                close_client_socket(clients, broadcast, client_socket, client_nickname)  # 关闭客户端连接
                break  # 退出循环
            elif message:
                # 处理接收到的消息
                parts = message.split(":", 1)  # 分割用户名和消息内容
                if len(parts) == 2:
                    username, message_content = parts
                    current_time = datetime.now().strftime("%H:%M:%S")
                    # 格式化消息，并打印
                    formatted_message = f"[{current_time}] {username}: {message_content}"
                    print(formatted_message)
                    # 广播消息给所有连接的客户端
                    broadcast(None, formatted_message)
                else:
                    # 如果消息格式不正确，发送错误消息
                    client_socket.send("错误的格式，消息未发送。".encode('utf-8'))
        except Exception as e:
            print(f"[!] Exception: {e}")  # 打印异常信息
            # 从clients列表中移除异常的客户端
            clients.remove(client_socket)
            client_socket.close()
            current_time = datetime.now().strftime("%H:%M:%S")
            print(f"\n[*] [{current_time}] {client_nickname} 因异常断开连接\n")  # 打印客户端异常断开信息
            broadcast(client_socket, f"\n[*] [{current_time}] {client_nickname} 因异常断开连接\n")  # 广播客户端异常断开信息
            break

# 全局函数，用于关闭客户端连接并广播断开连接消息
def close_client_socket(clients, broadcast, client_socket, client_nickname):
    try:
        # 从客户端列表中移除当前客户端
        clients.remove(client_socket)
        
        # 关闭socket连接
        client_socket.close()
        
        # 获取当前时间
        current_time = datetime.now().strftime("%H:%M:%S")
        
        # 广播客户端断开连接的消息
        print(f"\n[*] [{current_time}] {client_nickname} 已断开连接\n")
        broadcast(None, f"\n[*] [{current_time}] {client_nickname} 已断开连接\n")
    except Exception as e:
        print(f"[!] 关闭客户端连接时发生错误: {e}")

# 广播消息给所有客户端，除了target
def broadcast(target, message):
    for client in clients:
        if client != target:
            try:
                client.send(message.encode('utf-8'))  # 发送消息给客户端
            except Exception as e:
                print(f"[!] 无法发送消息到 {client.getpeername()}: {e}")

# 主循环，接受客户端连接
while True:
    client, address = server.accept()  # 接受新的客户端连接
    clients.append(client)  # 将新的客户端添加到客户端列表中

    client_thread = threading.Thread(target=handle_client, args=(client, address, broadcast))  # 创建处理客户端的新线程
    client_thread.start()  # 启动线程