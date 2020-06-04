from main.apis.amazon.amazon import *



class RequestClient:
    def __init__(self):
        self.amazon = AmazonCrawler()

    def request(self, taskDetail):
        """
        根据任务类型执行不同的api
        :param taskDetail:
        :return:
        """
        taskType = taskDetail['type']
        if taskType in ['amazonKeyword','amazonDetail','amazonComments']:
            return self.amazon.request(taskDetail)



