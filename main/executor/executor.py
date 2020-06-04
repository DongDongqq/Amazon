from main.db.db import *
from main.request.search import *
from main.utils.log import *
from main.setting import *
import json
import traceback
import time


class DataExecutor:

    def __init__(self):
        self.logger = Logger()
        self.redisClient = RedisClient(db=TASK_REDIS_PO)
        self.redisResultClient = RedisClient(db=TASK_RESULT_REDIS_PO)
        self.requestClient = RequestClient()

    def __add2Redis(self, taskDetail, result):
        """
        将结果加入Redis
        :param taskDetail:
        :return:
        """
        self.logger.info(u'返回正确结果')
        insertResult = False
        if 'timeout' in taskDetail:
            timeout = taskDetail['timeout']
        else:
            timeout = 300
        while not insertResult:
            try:
                insertResult = self.redisResultClient.getDB(host=TASK_REDIS_HOST, port=TASK_REDIS_PORT,
                                                            password=TASK_REDIS_PASSWORD,
                                                            db=TASK_RESULT_REDIS_PO).setex(name=taskDetail['key'],
                                                                                           time=int(timeout),
                                                                                           value=str(result))
                res = json.loads(result)
                if res['code'] != 200:
                    self.logger.info(str(res['msg']))
                self.logger.info('插入数据成功')
            except:
                # self.logger.error('redis结果插入失败')
                # print(traceback.format_exc())
                time.sleep(2)

    def __deal(self, taskDetail, index):
        """
        返回正确的结果
        :param index:
        :param taskDetail:
        :return:
        """
        self.logger.info("开始处理 " + taskDetail['key'])
        try:
            result = self.requestClient.request(taskDetail)
        except:
            time.sleep(2)
            result = self.requestClient.request(taskDetail)
        print('结果打印：', json.dumps(result, ensure_ascii=False,indent=4))
        try:
            if result and result['code'] != 401:
                result = json.dumps(result, ensure_ascii=False)
                self.__add2Redis(taskDetail, result)
            else:
                if index > 2:
                    result = json.dumps(result, ensure_ascii=False)
                    self.__add2Redis(taskDetail, result)
                else:
                    taskDetail['isproxy'] = False
                    self.__deal(taskDetail, index + 1)
        except:
            self.logger.error(u" 结果错误")
            pass

    def start(self, taskQueue):
        """
        循环取任务
        :return:
        """
        print("取任务", taskQueue)
        st = 0.1
        while True:
            try:
                task = self.redisClient.getDB(db=TASK_REDIS_PO).lpop(taskQueue)
                if task:
                    self.logger.info(u'接到任务')
                    self.logger.info(task)
                    taskDetail = json.loads(task)
                    self.__deal(taskDetail, 1)
                    st = 0.1
                else:
                    st = 1
            except:
                pass
            time.sleep(st)

    def test(self):
        # 亚马逊
        task = {
            'type': 'amazonDetail',
            'url': 'https://www.amazon.com/dp/B07TBWLS4T/ref=sspa_dk_detail_2?psc=1&pd_rd_i=B07TBWLS4T&pd_rd_w=aAzwf&pf_rd_p=48d372c1-f7e1-4b8b-9d02-4bd86f5158c5&pd_rd_wg=lvbRc&pf_rd_r=FYSKFSCNBAPGVKV376PV&pd_rd_r=dc8a340f-b7fc-424e-91c9-aacbadac9500&spLa=ZW5jcnlwdGVkUXVhbGlmaWVyPUFOMVFDS05TSTFQN1kmZW5jcnlwdGVkSWQ9QTA1OTk4MjkyVzRGUDNIN0dMVEVXJmVuY3J5cHRlZEFkSWQ9QTA5OTk3ODMyS1lCSENYRDBKM1EyJndpZGdldE5hbWU9c3BfZGV0YWlsJmFjdGlvbj1jbGlja1JlZGlyZWN0JmRvTm90TG9nQ2xpY2s9dHJ1ZQ==',
            'countryCode': 'CN',
            'language': '',
            'key':'',
            'isproxy': False

        }
        if task:
            self.logger.info(u'接到任务')
            self.logger.info(task)
            if type(task) == dict:
                taskDetail = task
            else:
                taskDetail = json.loads(task)
            self.__deal(taskDetail, 1)


if __name__ == '__main__':
    ex = DataExecutor()
    ex.test()
