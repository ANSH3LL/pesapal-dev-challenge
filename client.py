import socket
import threading

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('127.0.0.1', 5000))

def receive_messages():
    '''
    Receives and displays messages from the server.
    Also executes commands from higher-ranked clients. Runs in a thread
    '''
    while True:
        data = sock.recv(4096).decode('utf-8')
        if not data:
            print('\nThe server has disconnected')

            sock.close()
            break

        if data.startswith('/'):
            print(f'\nExecuting command: {data[1:]}')
        else:
            print(f'\n{data}')

threading.Thread(target = receive_messages).start()

while True:
    command = input('Enter command: ')
    try:
        sock.send(command.encode('utf-8'))
    except:
        break
