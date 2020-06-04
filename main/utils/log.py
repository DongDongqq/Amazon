# coding=utf-8
from fishbase.fish_logger import *
from fishbase.fish_file import *


class Logger:
    def __init__(self):
        logpath = os.path.join(os.getcwd(), "log")
        if not os.path.exists(logpath):
            os.mkdir(logpath)
        log_abs_filename = get_abs_filename_with_sub_path('log', 'amazon.log')[1]
        set_log_file(log_abs_filename)

    def info(self, log):
        logger.info(log)

    def warn(self, log):
        logger.warn(log)

    def error(self, log):
        logger.error(log)
