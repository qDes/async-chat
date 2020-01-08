import json
import socket
import os

from dotenv import load_dotenv
from tkinter import *
from tkinter import Tk, Label, Button, Entry, messagebox


def registration(nickname):
    load_dotenv()
    TCP_IP = os.environ['host']
    TCP_WRITE = int(os.environ['port_write'])
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((TCP_IP, TCP_WRITE))
    s.send(b'\n')
    data = s.recv(1024)
    #print('1',data)
    nickname += '\n\n'
    s.send(nickname.encode())
    data = s.recv(1024)
    #print('2', data)
    s.send(b'\n')
    data = s.recv(1024) 
    #print('3', data)
    s.close()
    reg_data = data.decode().split('\n')[0]
    reg_data = json.loads(reg_data)
    print(reg_data)
    account_hash = reg_data.get("account_hash")
    return account_hash


class RegistrationGUI:
    def __init__(self, master):
        self.master = master
        master.title("Registration")

        #self.label = Label(master, text="This is our first GUI!")
        #self.label.pack()
        
        self.entry = Entry(width=50)
        self.entry.pack()

        self.greet_button = Button(master, text="Greet", command=self.greet)
        self.greet_button.pack()


    def greet(self):
        msg = self.entry.get()
        acc_hash = registration(msg)

        messagebox.showinfo("Info", f"{acc_hash}")
        self.master.quit()

if __name__ == "__main__":
    root = Tk()
    my_gui = RegistrationGUI(root)
    root.mainloop()

