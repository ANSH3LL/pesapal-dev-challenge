import sys
import socket
import threading

class RankedClient:
    '''
    Client data class used as a convenience
    '''
    def __init__(self, socket_object, rank):
        '''
        Initialize a ranked client that keeps track of its rank

        :param socket_object: A client's socket object
        :param rank: A client's rank
        '''
        self.socket = socket_object
        self.rank = rank

class Server:
    def __init__(self, max_clients):
        '''
        Initializes the server

        :param max_clients: The maximum number of clients who are allowed to connect.
        Must be an integer larger than 1
        '''
        if max_clients < 2:
            raise ValueError('max_clients must be larger than 1')

        self.port = 5000
        self.next_rank = 0

        self.client_registry = {}
        self.max_clients = max_clients

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start_server(self):
        '''
        Start accepting connections from clients. Server is bound to all interfaces
        '''
        self.socket.bind(('', self.port))
        self.socket.listen() # Uses default backlog value

        print(f'Listening for client connections on port {self.port}')
        print(f'Maximum allowed clients: {self.max_clients}')

        listener = threading.Thread(target = self.handle_connections)
        listener.start()
        listener.join()

        self.socket.close()

    def handle_connections(self):
        '''
        Handle client connections. Max clients and ranking is enforced here
        '''
        while True:
            client, address = self.socket.accept()

            if self.next_rank == self.max_clients:
                client.send(b'Server is currently full, try again later')
                client.close()

                print(f'Connection from {address[0]} was rejected. Server is full')
            else:
                rank = self.next_rank
                print(f'Accepted connection from {address[0]}. Assigned rank {rank}')

                rclient = RankedClient(client, rank)

                self.client_registry[rank] = rclient
                client.send(f'You are rank number {rank}'.encode('utf-8'))

                self.broadcast(f'A new client with rank number {rank} has connected to the server', client)

                self.next_rank += 1
                threading.Thread(target = self.handle_client, args = (rclient,)).start()

    def handle_client(self, ranked_client):
        '''
        Handles messages received from a single client. Runs in a thread

        :param ranked_client: A RankedClient object. Used to send and receive messages
        '''
        while True:
            try:
                message = ranked_client.socket.recv(4096).decode('utf-8')
                self.relay_command(ranked_client, message)
            except ConnectionResetError:
                rank = ranked_client.rank
                ranked_client.socket.close()

                del self.client_registry[rank]

                print(f'Client with rank {rank} has disconnected')
                self.broadcast(f'Client with rank {rank} has disconnected')

                self.promote(rank)
                break

    def broadcast(self, message, exclude = None):
        '''
        Sends status messages to all connected clients, with optional exclusion

        :param message: The message to broadcast
        :param exclude: The client socket object to exclude from the broadcast. Optional
        '''
        for key, value in self.client_registry.items():
            if value.socket == exclude:
                continue
            try:
                value.socket.send(message.encode('utf-8'))
            except OSError:
                pass

    def promote(self, rank):
        '''
        Promotes all clients below the given rank

        :param rank: An abandoned rank that needs filling
        '''

        print(f'Promoting clients below rank {rank}')

        for key, value in self.client_registry.copy().items():
            if value.rank == 0:
                continue

            if key > rank:
                self.client_registry[key - 1] = value
                value.rank -= 1

                try:
                    value.socket.send(f'You have been promoted to rank {value.rank}'.encode('utf-8'))
                except OSError:
                    pass

        self.next_rank -= 1

    def relay_command(self, ranked_client, command):
        '''
        Decides who should receive the given command based on their ranking. Also ensures commands have valid syntax

        :param ranked_client: The RankedClient object belonging to the client sending this command
        :param command: The command to be executed
        '''
        if not command.startswith('/'):
            try:
                ranked_client.socket.send(b'Invalid command syntax. Prefix your command with "/" and try again')
            except OSError:
                pass
            return None

        for x in range(ranked_client.rank + 1, self.next_rank):
            try:
                self.client_registry[x].socket.send(command.encode('utf-8'))
            except OSError:
                pass

# Run the server if this script is not being used as a module
if __name__ == '__main__':
    max_clients = 3

    if len(sys.argv) > 1:
        try:
            max_clients = int(sys.argv[1])
        except:
            pass

    server = Server(max_clients)
    server.start_server()
