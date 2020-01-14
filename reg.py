import json
import socket
import os

from dotenv import load_dotenv
from tkinter import Tk, Label, Button, Entry, messagebox


def save_account(token):
    with open('.token', 'w') as f:
        to_file = f"token = {token}"
        f.write(to_file)


def register_user(nickname):
    load_dotenv()
    TCP_IP = os.environ['host']
    TCP_HOST = int(os.environ['port_write'])
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((TCP_IP, TCP_HOST))
    data = s.recv(1024)
    s.send(b'\n')
    data = s.recv(1024)
    nickname += '\n'
    s.send(nickname.encode())
    data = s.recv(1024)
    s.close()
    reg_data = data.decode().split('\n')[0]
    reg_data = json.loads(reg_data)
    account_hash = reg_data.get("account_hash")
    return account_hash


class RegistrationGUI:
    def __init__(self, master):
        self.master = master
        master.title("Registration")
        master.geometry("500x100")
        self.label = Label(master, text="Введите ник ниже:")
        self.label.pack()
        self.entry = Entry(master, width=25)
        self.entry.pack()
        self.greet_button = Button(master, text="Регистрация", command=self.reg_user)
        self.greet_button.pack()


    def reg_user(self):
        nickname = self.entry.get()
        account_hash = register_user(nickname)
        save_account(account_hash)
        messagebox.showinfo("Info", f"{nickname} зарегестирован. Перезапустите приложение.")
        self.master.quit()


if __name__ == "__main__":
    root = Tk()
    my_gui = RegistrationGUI(root)
    root.mainloop()
