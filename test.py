from MaxKB import MaxKBApi, MaxKB

max = MaxKB()

max = max.getMaxKBApi()

chatId = max.get_chat()["data"]

print(chatId)

req = max.send_message(chatId, "你好")

print(req)