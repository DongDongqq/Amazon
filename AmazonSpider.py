import multiprocessing
import time
from main.scheduler import *
from main.apis.amazon.amazon import AmazonCrawler

if __name__ == "__main__":
    multiprocessing.freeze_support()
    scheduler = Scheduler()
    scheduler.run()
    time.sleep(5)
    print("输入指令1停止所有进程")
    while True:
        action = input("请输入命令：")
        action = int(action)
        if action == 1:
            scheduler.term()
            break

    # crawler = AmazonCrawler()
    # crawler.test_jp()