import functools
import time

def retry_by_msg(retry_time=3, sleep_time=1, msg='请求太过频繁，请稍后再试'):
    '''
    重试装饰器
    通过错误消息判断是否进行重试,用于存在失败概率的接口
    :param retry_time: 重试次数
    :param sleep_time: 休眠时间
    :param msg: 错误消息
    :return:
    '''
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            for _ in range(retry_time):
                result = func(*args, **kw)
                if result.get('msg') == msg:
                    print(f'retrying:{_} func:{func.__name__}')
                    time.sleep(sleep_time)
                    continue
                else:
                    return result

            return func(*args, **kw)
        return wrapper
    return decorator