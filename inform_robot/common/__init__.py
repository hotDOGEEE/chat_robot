import requests

url = "http://im-api.skyunion.net/msg"


def message(func):
    def temp(*args, **kwargs):
        rooms, content, at_usr = func(*args, **kwargs)
        body = {"token": "xxxx",
                "target": "group",
                "room": None,
                "title": "我是机器人",
                "content_type": "1",
                "content": content,
                "at_user": at_usr}
        if isinstance(rooms, str):
            body["room"] = rooms
            requests.post(url, body)
        elif isinstance(rooms, set):
            for i in rooms:
                body["room"] = i
                requests.post(url, body)
    return temp

