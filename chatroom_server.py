# By ViudiraTech
# GPL-2.0

import socket
import threading

print('Paizer服务端\n')

def get_local_ipv4():
    # 获取所有网络接口的信息
    interfaces = socket.getaddrinfo(socket.gethostname(), None)
    for interface in interfaces:
        address = interface[4][0]
        # 检查是否为IPv4地址
        if address.startswith('192.168') or address.startswith('10.') or address.startswith('172.'):
            return address
    return '无法获取IPv4内网地址'

local_ipv4 = get_local_ipv4()
print(f"[*] 当前服务器内网地址: {local_ipv4}")

# 服务端的IP地址和端口号
server_ip = '0.0.0.0'  # 监听所有公网IP
server_port = 21156

# 创建socket对象
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((server_ip, server_port))
server.listen(5)
print(f"[*] 正在监听 {server_ip}:{server_port}\n")

# 存储所有客户端的列表
clients = []

def handle_client(client_socket, client_address, broadcast):
    # 接收客户端的昵称
    client_nickname = client_socket.recv(1024).decode('utf-8').strip(': ')
    print(f"[*] [{address[0]}] {client_nickname} 加入了服务器")
    broadcast(client_socket, f"[*] [{address[0]}] {client_nickname} 加入了服务器")
    
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if message:
                print(f"[{client_address[0]}] {message}")
                # 广播消息给所有连接的客户端，包括发送者
                broadcast(None, f"[{client_address[0]}] {message}")
            else:
                # 客户端断开连接
                clients.remove(client_socket)
                client_socket.close()
                print(f"[*] [{client_address[0]}] {client_nickname} 已断开连接")
                broadcast(client_socket, f"[*] [{client_address[0]}] {client_nickname} 已断开连接")  # 广播断开连接消息
                break
        except Exception as e:
            print(f"[!] Exception: {e}")
            # 从clients列表中移除异常的客户端
            clients.remove(client_socket)
            client_socket.close()
            print(f"[*] [{client_address[0]}] {client_nickname} 已断开连接")
            broadcast(client_socket, f"[*] [{client_address[0]}] {client_nickname} 已断开连接")  # 广播断开连接消息
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
#   print(f"[*] [{address[0]}] 加入了服务器")
    clients.append(client)

    # 创建一个新线程来处理客户端
    client_thread = threading.Thread(target=handle_client, args=(client, address, broadcast))
    client_thread.start()