"""
Серверное приложение для соединений
"""
import asyncio
from asyncio import transports


class ClientProtocol(asyncio.Protocol):
    login: str
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server
        self.login = None

    def data_received(self, data: bytes):
        decoded = data.decode()
        print(decoded)

        if self.login is None:
            # login:User
            if decoded.startswith("login:"):
                temp_login = decoded.replace("login:", "").replace("\r\n", "")
                login_list = []
                for client in self.server.clients:
                    login_list.append(client.login)

                if temp_login in login_list:
                    self.transport.write(
                        f"Логин {temp_login} занят, попробуйте другой!".encode()
                    )
                    self.transport.close()
                else:
                    self.login = temp_login
                    self.transport.write(
                        f"Привет, {self.login}!".encode()
                    )
        else:
            self.send_message(decoded)

    def send_history(self, msg_number):
        history = "\r\n".join(self.server.history[-msg_number:])
        self.transport.write(history.encode())

    def send_message(self, message):
        format_string = f"<{self.login}> {message}"
        encoded = format_string.encode()
        for client in self.server.clients:
            if client.login != self.login:
                client.transport.write(encoded)
        self.server.history.append(format_string)

    def connection_made(self, transport: transports.Transport):
        self.transport = transport
        self.server.clients.append(self)
        print("Соединение установлено")
        if len(self.server.history) != 0:
            self.send_history(10)
        else:
            self.transport.write(str("--Кажется, тут еще не было сообщений!--").encode())

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Соединение разорвано")


class Server:
    clients: list
    history: list

    def __init__(self):
        self.clients = []
        self.history = []

    def create_protocol(self):
        return ClientProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.create_protocol,
            "127.0.0.1",
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()
try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
