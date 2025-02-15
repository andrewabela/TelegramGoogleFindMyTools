#
#  GoogleFindMyTools - A set of tools to interact with the Google Find My API
#  Copyright © 2024 Leon Böttger. All rights reserved.
#
from NovaApi.ListDevices.nbe_list_devices import list_devices
from Telegram.server import TelegramServer


if __name__ == '__main__':
    telegram_server = TelegramServer()
    telegram_server.send_message("Server started\nSend any message to get started")

    while True:
        try:
            telegram_server.get_message(fast=False)# start waiting until a new message is received
            list_devices(telegram_server=telegram_server)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(e)
            telegram_server.send_message(f"Error: {e}")