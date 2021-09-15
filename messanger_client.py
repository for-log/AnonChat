import base64
from threading import Thread
from Crypto import Random
from Contants import *
import rsa
from Crypto.Cipher import AES
import rsa.randnum

def pad(s):
    return s + b"\0" * (AES.block_size - len(s) % AES.block_size)

class Client:
    def __init__(self, port):
        self.ip = socket.gethostbyname(socket.gethostname())
        self.port = port
        self.socket = socket.socket()
        try:
            self.socket.connect((self.ip, self.port))
        except ConnectionRefusedError:
            print("Сервер выключен, подключитесь позже!")
        self.write_cond = 0
        (self.pub_key, self.priv_key) = rsa.newkeys(512)
        self.dialog_key = None
        self.commands = []

    def listen(self):
        while 1:
            message = self.socket.recv(4096).decode()
            if "}{" in message:
                self.split_commands(message)
            else:
                self.commands.append(message)
            self.executor()

    def split_commands(self, message):
        prev = ""
        command = ""
        for i in range(len(message)):
            if prev + message[i] == "}{":
                self.commands.append(command)
                command = ""
            prev = message[i]
            command += message[i]
        self.commands.append(command)

    def executor(self):
        size = len(self.commands)
        for i in range(size):
            data = json.loads(self.commands[i])
            if data.get("event") == register_server_command:
                self.auth()
            elif data.get("event") == empty_free_users_list:
                print("Подождите пока появится свободное подключение!")
            elif data.get("event") == server_find_dialog:
                print("Появилось новое подключение! Можете начать общаться:")
                self.dialog_key = rsa.PublicKey.load_pkcs1(data.get("dialog_keys"), 'PEM')
                self.write_cond = 1
            elif data.get("event") == message_server_command:
                message = data.get("message")
                key = data.get("key")
                print(f'{data.get("from")}: {self.decode_message(message, key)}')
            elif data.get("event") == leave_dialog:
                print("Собеседник вышел из диалога, ищем новое подключение...")
                self.write_cond = 0
                self.socket.send(json.dumps({"event": client_find_dialog}).encode())
            elif data.get("event") == user_does_exist:
                print("Пользователь с таким именем уже существует, придумайте другое имя!")
                self.auth()
        self.commands = self.commands[size:]

    def auth(self):
        login = input("Введите логин: ")
        self.socket.send(json.dumps({
            "event": register_client_command,
            "login": login,
            "key": self.pub_key.save_pkcs1().decode()
        }).encode())

    def encode_message(self, message):
        message = pad(message)
        aes_key = rsa.randnum.read_random_bits(128)
        iv = Random.new().read(AES.block_size)
        obj = AES.new(aes_key, AES.MODE_CBC, iv)
        encode_message = iv + obj.encrypt(message)
        encrypted_aes_key = rsa.encrypt(aes_key, self.dialog_key)
        return base64.b64encode(encode_message).decode("utf-8"), base64.b64encode(encrypted_aes_key).decode("utf-8")

    def decode_message(self, message, key):
        message = base64.b64decode(message)
        key = base64.b64decode(key)
        iv = message[:AES.block_size]
        aes_key = rsa.decrypt(key, self.priv_key)
        obj = AES.new(aes_key, AES.MODE_CBC, iv)
        return obj.decrypt(message[AES.block_size:]).rsplit(b"\0")[0].decode()

    def write(self):
        while 1:
            if self.write_cond:
                message, key = self.encode_message(input().encode())
                if self.write_cond:
                    data = json.dumps({
                        "event": message_client_command,
                        "message": message,
                        "key": key
                    })
                    self.socket.send(data.encode())

    def main(self):
        Thread(target=self.listen).start()
        self.write()

if __name__ == "__main__":
    c = Client(8080)
    c.main()