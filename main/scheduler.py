from main.executor.executor import *
from main.setting import *
from multiprocessing import Process


class Scheduler:
    def __init__(self):

        self.processes = []

    def start(self, task):
        """
        开始任务
        :param task:
        :return:
        """
        executor = DataExecutor()
        executor.start(task)

    def amazon(self):
        """
        亚马逊任务开启
        :return:
        """
        print('亚马逊服务开启')
        # 亚马逊
        amazon_keyword_process = Process(target=self.start, args=(TASK_AMAZON_KEYWORD_QUEUE,))
        amazon_keyword_process.start()
        self.processes.append(amazon_keyword_process)

        amazon_detail_process = Process(target=self.start, args=(TASK_AMAZON_DETAIL_QUEUE,))
        amazon_detail_process.start()
        self.processes.append(amazon_detail_process)

        amazon_comments_process = Process(target=self.start, args=(TASK_AMAZON_COMMENTS_QUEUE,))
        amazon_comments_process.start()
        self.processes.append(amazon_comments_process)

    def term(self):
        print('%d to term child process' % os.getpid())

        try:
            for p in self.processes:
                print('process %d-%d terminate' % (os.getpid(), p.pid))
                if p.is_alive:
                    p.terminate()
                    print('stop process')
                    p.join()
        except Exception as e:
            print(str(e))

    def run(self):
        """
        启动服务
        :return:
        """
        print('亚马逊api服务开始运行')

        # 亚马逊开启
        self.amazon()



