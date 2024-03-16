# By ViudiraTech
# GPL-2.0 LICENSE

import socket
import threading
from datetime import datetime

def get_local_ipv4():
    interfaces = socket.getaddrinfo(socket.gethostname(), None)
    for interface in interfaces:
        address = interface[4][0]
        if address.startswith('192.168') or address.startswith('10.') or address.startswith('172.'):
            return address
    return '无法获取IPv4内网地址'

def get_server_port():
    while True:
        input_port = input("设置服务端监听端口（留空为21156）：")
        if not input_port:
            port = 21156
        else:
            try:
                port = int(input_port)
                if 0 < port < 65536:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as test_socket:
                        try:
                            test_socket.bind(('localhost', port))
                        except PermissionError:
                            print(f"端口 {port} 已被占用或不允许访问。请重新输入端口号。")
                            continue
                else:
                    print("端口号无效，请输入1到65535之间的数字。")
            except ValueError:
                print("请输入一个有效的端口号。")
        return port

print('Paizer服务端\n')

server_port = get_server_port()
print()
print(f"[*] 当前服务端监听端口: {server_port}")

local_ipv4 = get_local_ipv4()
print(f"[*] 当前服务器内网地址: {local_ipv4}")

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('0.0.0.0', server_port))
server.listen(5)
server_ip, server_port = server.getsockname()
print(f"[*] 正在监听 {server_ip}:{server_port}\n")

clients = []

def handle_client(client_socket, client_address, broadcast):
    # 接收客户端的昵称
    client_nickname = client_socket.recv(1024).decode('utf-8').strip(': ')
    current_time = datetime.now().strftime("%H:%M:%S")
    print(f"[*] [{current_time}] {client_nickname} 加入了服务器")
    broadcast(client_socket, f"[*] [{current_time}] {client_nickname} 加入了服务器")
    
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if message:
                # 假设消息格式为 "用户名: 消息内容"
                parts = message.split(":", 1)  # 分割用户名和消息内容
                if len(parts) == 2:
                    username, message_content = parts
                    current_time = datetime.now().strftime("%H:%M:%S")
                    # 格式化消息，包含时间戳和消息内容
                    formatted_message = f"[{current_time}] {username}: {message_content}"
                    print(formatted_message)
                    # 广播消息给所有连接的客户端，包括发送者
                    broadcast(None, formatted_message)
                else:
                    # 如果消息格式不正确，发送错误消息
                    client.send("错误的格式，消息未发送。".encode('utf-8'))
        except Exception as e:
            print(f"[!] Exception: {e}")
            # 从clients列表中移除异常的客户端
            clients.remove(client_socket)
            client_socket.close()
            current_time = datetime.now().strftime("%H:%M:%S")
            print(f"[*] [{current_time}] {client_nickname} 已断开连接")
            broadcast(client_socket, f"[*] [{current_time}] {client_nickname} 已断开连接")  # 广播断开连接消息
            break

def broadcast(target, message):
    # 广播消息给所有客户端，除了target
    for client in clients:
        if client != target:
            try:
                client.send(message.encode('utf-8'))
            except Exception as e:
                print(f"[!] 无法发送消息到 {client.getpeername()}: {e}")

while True:
    client, address = server.accept()
    clients.append(client)

    client_thread = threading.Thread(target=handle_client, args=(client, address, broadcast))
    client_thread.start()