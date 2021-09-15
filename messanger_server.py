import select
import random
from Contants import *
import copy

class Counter:
    def __init__(self, start=0):
        self.count = start

    def __call__(self):
        self.count += 1
        return self.count - 1

    @property
    def max(self):
        return self.count

class User:
    def __init__(self, idx, login, public_key):
        self.id = idx
        self.login = login
        self.pub_key = public_key
        self.socket = None
        self.dialog_id = None

    def connect(self, socket):
        self.socket = socket

    def disconnect(self):
        self.socket.close()
        self.socket = None

    def send(self, data):
        if self.socket is not None:
            self.socket.send(data.encode())

    def set_dialog(self, idx):
        self.dialog_id = idx

    def clear_dialog(self):
        self.dialog_id = None
        self.send(json.dumps({"event": leave_dialog}))

class Server:
    def __init__(self, port):
        self.ip = socket.gethostbyname(socket.gethostname())
        print(self.ip)
        self.port = port
        self.socket = socket.socket()
        self.socket.bind((self.ip, self.port))
        self.socket.listen(100)
        self.conns = [self.socket]
        self.registered = {}
        self.names = {}
        self.counter = Counter()
        self.dialogs = []
        self.variables_command = {
            register_client_command: self.user_checker,
            message_client_command: self.send_message,
            client_find_dialog: self.find_dialog
        }
        self.tasks = []

    def listen(self):
        while 1:
            read, write, err = select.select(self.conns, self.conns, [])
            if read:
                for conn in read:
                    if conn == self.socket:
                        self.accept()
                    else:
                        self.recv(conn)

    def accept(self):
        sock, _ = self.socket.accept()
        sock.send(json.dumps({"event": register_server_command}).encode())
        self.conns.append(sock)

    def split_commands(self, message):
        prev = ""
        command = ""
        for i in range(len(message)):
            if prev + message[i] == "}{":
                self.tasks.append(command)
                command = ""
            prev = message[i]
            command += message[i]
        self.tasks.append(command)

    def recv(self, connect):
        try:
            message = connect.recv(2048).decode()
            if len(message) > 0:
                print("[LOG:message]", message)
                if "}{" in message:
                    self.split_commands(message)
                else:
                    self.tasks.append(message)
                self.executor(connect)
            else:
                print("[LOG:disconnect]")
                self.disconnect(connect)
        except ConnectionResetError:
            self.disconnect(connect)

    def executor(self, conn):
        size = len(self.tasks)
        for i in range(size):
            try:
                data = json.loads(self.tasks[i])
                if data.get("event") in self.variables_command:
                    self.variables_command[data.get("event")](data, conn)
                else:
                    conn.send(json.dumps({"event": event_doest_exist}).encode())
            except json.decoder.JSONDecodeError:
                pass
        self.tasks = self.tasks[size:]

    def user_checker(self, data, conn):
        login = data.get("login")
        if login not in self.names:
            self.register(conn, login, data.get("key"))
        else:
            conn.send(json.dumps({"event": user_does_exist}).encode())

    def register(self, conn, login, pub_key):
        u = User(self.counter(), login, pub_key)
        self.names[conn] = login
        self.registered[conn] = u
        u.connect(conn)
        self.find_dialog(None, conn)

    def find_dialog(self, data, conn):
        users = copy.copy(self.registered)
        for user in self.dialogs:
            users.pop(user, key_doest_exist)
        users.pop(conn, key_doest_exist)
        if len(users) == 0:
            conn.send(json.dumps({"event": empty_free_users_list}).encode())
            return 0
        list_user = [self.registered[conn], self.registered[random.choice(list(users.keys()))]]
        for i in range(len(list_user)):
            self.dialogs.append(list_user[i].socket)
            list_user[i].set_dialog(list_user[int(not i)])
            list_user[i].send(json.dumps({"event": server_find_dialog, "dialog_keys": list_user[int(not i)].pub_key}))

    def send_message(self, data, conn):
        user = self.registered[conn]
        if user.dialog_id is not None:
            dialog = user.dialog_id
            dialog.send(json.dumps({
                "event": message_server_command,
                "from": user.login,
                "message": data.get("message"),
                "key": data.get("key")
            }))

    def disconnect(self, conn):
        self.conns.remove(conn)
        if conn in self.registered:
            user = self.registered[conn]
            user.disconnect()
            if conn in self.dialogs:
                dialog = user.dialog_id
                dialog.clear_dialog()
                self.dialogs.remove(conn)
                self.dialogs.remove(dialog.socket)
            self.registered.pop(conn, key_doest_exist)

if __name__ == "__main__":
    s = Server(8080)
    s.listen()





