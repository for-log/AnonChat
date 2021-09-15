import socket
import json

register_server_command = 0x1
register_client_command = 0x2
message_server_command = 0x3
message_client_command = 0x4
server_find_dialog = 0x5
client_find_dialog = 0x6
leave_dialog = 0x7

user_doesnt_exist = 0x10
user_does_exist = 0x11
password_wrong = 0x12
empty_free_users_list = 0x13
user_keys = 0x14

key_doest_exist = 0x20
event_doest_exist = 0x21
