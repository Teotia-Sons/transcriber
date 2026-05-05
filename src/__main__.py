from mongoengine import connect

from config import Config

from .server import Server
from .tracing import setup_tracing


def main():
    setup_tracing()
    # Close idle connections to handle system sleep/wake cycles
    connect(host=Config.MONGO_URI, maxIdleTimeMS=180000)
    server = Server()
    server.run()


if __name__ == "__main__":
    main()
