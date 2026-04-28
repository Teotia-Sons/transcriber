from mongoengine import connect

from config import Config

from .server import Server
from .tracing import setup_tracing


def main():
    setup_tracing()
    connect(host=Config.MONGO_URI)
    server = Server()
    server.run()


if __name__ == "__main__":
    main()
