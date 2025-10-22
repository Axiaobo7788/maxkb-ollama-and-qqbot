import requests


class MaxKBApi:
    def __init__(self, config: dict):
        self.url = config["base_url"]
        self.apiKey = config["api_key"]

    def get_data(self, message: dict, stream: bool = False) -> dict:
        return {
            "message": message,
            "stream": stream
        }

    def get_chat(self) -> dict:
        return requests.get(
            url=self.url + "/chat/api/open",
            headers={
                "Authorization": f"Bearer {self.apiKey}",
            }
        ).json()

    def send_message(self, chatId: str, message: str, **kwargs) -> dict:
        data: dict = self.get_data(message=message)

        return requests.post(
            url=self.url + f"/chat/api/chat_message/{chatId}",
            data=data,
            headers={
                "Authorization": f"Bearer {self.apiKey}",
            }
        ).json()
