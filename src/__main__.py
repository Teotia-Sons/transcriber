from mongoengine import connect

from config import Config
from .tracing import setup_tracing
from .server import Server


def main():
    setup_tracing()
    connect(host=Config.MONGO_URI)
    server = Server()
    server.run()


if __name__ == "__main__":
    main()
