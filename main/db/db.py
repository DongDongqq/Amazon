import redis
from main.setting import *


class RedisClient:
    def __init__(self, host=TASK_REDIS_HOST, port=TASK_REDIS_PORT, password=TASK_REDIS_PASSWORD, db=TASK_REDIS_PO):
        """
        初始化
        :param host:
        :param port:
        :param password:
        """
        self.db = self.__doConnect(host=host, port=port, password=password, db=db)

    def __doConnect(self, host=TASK_REDIS_HOST, port=TASK_REDIS_PORT, password=TASK_REDIS_PASSWORD, db=TASK_REDIS_PO):
        self.db = redis.StrictRedis(host=host, port=port, password=password, db=db, decode_responses=True)
        return self.db

    def getDB(self, host=TASK_REDIS_HOST, port=TASK_REDIS_PORT, password=TASK_REDIS_PASSWORD, db=TASK_REDIS_PO):
        if not self.db:
            self.db = self.__doConnect(host=host, port=port, password=password, db=db)
        return self.db

    def addAccountQueue(self, account, queue=ACCOUNT_QUEUE):
        return self.getDB(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, db=REDIS_PO).lpush(queue,
                                                                                                        str(account))

    def getAccountQueue(self, queue=ACCOUNT_QUEUE):
        return self.getDB(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, db=REDIS_PO).rpop(queue)
