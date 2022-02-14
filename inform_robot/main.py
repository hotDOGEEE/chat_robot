from typing import Optional, Awaitable
import tornado.web
from tornado.ioloop import IOLoop
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.tornado import TornadoScheduler
from pymongo.mongo_client import MongoClient
import requests
from logzero import logger

myclient = MongoClient("localhost", 27017)
scheduler = TornadoScheduler(timezone='Asia/Shanghai', job_defaults={'misfire_grate_time': 3600})
scheduler.add_jobstore("mongodb",
                       database="chat_events",
                       collection="example_jobs",
                       client=myclient)

config_events = myclient["chat_events"]["events"]


def sm(rooms, content:str, at_usr="all"):
    url = "http://xxx"
    body = {"token": "xxxxx",
            "target": "group",
            "room": None,
            "title": "我是机器人",
            "content_type": "1",
            "content": content,
            "at_user": at_usr}
    if isinstance(rooms, str):
        body["room"] = rooms
        requests.post(url, body)
    elif isinstance(rooms, set) or isinstance(rooms, list):
        for i in rooms:
            body["room"] = i
            requests.post(url, body)
    else:
        raise
    logger.info("请求发送成功")


def jobs_update():
    scheduler.remove_all_jobs()
    logger.info("任务更新，清除历史任务")
    for x in config_events.find():
        logger.info(f"成功添加任务:{x}")
        scheduler.add_job(func=sm, trigger=CronTrigger.from_crontab(x["time_rule"]), args=[x["rooms"], x["content"], x["at_usr"]])
    logger.info("任务加载完毕")


class AddJob(tornado.web.RequestHandler):

    def data_received(self, chunk: bytes) -> Optional[Awaitable[None]]:
        pass

    def get(self):
        rooms = self.get_query_arguments("rooms")
        content = self.get_query_argument("content")
        at_usr = self.get_query_arguments("at_usr")
        time_rule = self.get_query_argument("time_rule")
        usrs = str()
        for u in at_usr:
            usrs += u+","
        config_events.insert_one({"rooms": rooms, "content": content, "at_usr": usrs, "time_rule": time_rule})
        logger.info("收到添加任务请求")
        jobs_update()


class JobList(tornado.web.RequestHandler):

    def data_received(self, chunk: bytes) -> Optional[Awaitable[None]]:
        pass

    def get(self):
        for c in config_events.find():
            c.pop("_id")
            self.write(c)
        logger.info("已返回所有任务列表")


class DelJob(tornado.web.RequestHandler):

    def data_received(self, chunk: bytes) -> Optional[Awaitable[None]]:
        pass

    def post(self):
        target_data = eval(self.request.body.decode("utf-8"))
        config_events.find_one_and_delete(target_data)
        logger.info("已删除任务")
        jobs_update()


if __name__ == '__main__':
    scheduler.start()
    jobs_update()
    app = tornado.web.Application([(r"/addjob", AddJob),
                                   (r"/job_list", JobList),
                                   (r"/deljob", DelJob)])
    app.listen(9457)
    try:
        IOLoop.instance().start()
    except Exception as e:
        logger.warning(e)