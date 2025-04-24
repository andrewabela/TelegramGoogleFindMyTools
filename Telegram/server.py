import os
import requests
import time

latest_message = None


class TelegramServer:
    def __init__(self):
        self.token = os.environ.get("telegram_api_key")
        if not self.token:
            raise ValueError("Missing telegram_api_key environment variable")
        self.chat_id = os.environ.get("authorized_telegram_chat_id")
        self.debug = os.environ.get("debug") == "True"
        self.url = f"https://api.telegram.org/bot{self.token}"
        self.last_message_time_stamp = (
            time.time()
        )  # used to ony check for new messages received after the lest message was sent
        self.last_msg_id = 0
        self.last_message_id = ""

    def send_message(self, message: str, required=True):
        if required or self.debug:
            url = f"{self.url}/sendMessage"
            body = {"chat_id": self.chat_id, "text": message}
            response = requests.post(url, json=body)
            # print(response.text)
            self.last_message_time_stamp = time.time()

    def get_message(self, fast=True):
        url = f"{self.url}/getUpdates"
        body = {"offset": self.last_msg_id}
        response = requests.post(url, json=body)
        last_result = response.json()["result"][-1]["message"]
        if (
            (float(self.last_message_time_stamp) < float(last_result["date"]))
            and (self.last_message_id != last_result["message_id"])
        ) and str(self.chat_id) == str(last_result["chat"]["id"]):
            print("new message received")
            self.last_message_time_stamp = float(last_result["date"]) + float(1)
            self.last_message_id = last_result["message_id"]
            print(last_result["text"])
            return last_result["text"]
        else:
            time.sleep(0.5)
            if fast:
                return self.get_message()  # recursive call to recheck for new messages


# ts = TelegramServer()
# ts.send_message("Server started")

# while True:
#     try:
#         time.sleep(2)
#         ts.send_message(ts.get_message())
#     except KeyboardInterrupt:
#         break
