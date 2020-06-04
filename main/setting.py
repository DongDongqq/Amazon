################任务redis
# 数据库地址 cookie
REDIS_HOST = 'r-wz9l7e75bkfetxr8dxpd.redis.rds.aliyuncs.com'
# redis端口
REDIS_PORT = 6322
# redis password
REDIS_PASSWORD = 'AX754fc66c#W5190a202'
# 位置
REDIS_PO = "3"
########## cookies
ACCOUNT_QUEUE = 'AmazonCookieQueue'

# 数据库地址 任务
TASK_REDIS_HOST = 'r-wz9l7e75bkfetxr8dxpd.redis.rds.aliyuncs.com'
# 端口
TASK_REDIS_PORT = 6322
# 密码
TASK_REDIS_PASSWORD = 'AX754fc66c#W5190a202'
# task位置
TASK_REDIS_PO = "1"
# result 位置
TASK_RESULT_REDIS_PO = "2"

########亚马逊
# 亚马逊关键词搜索
TASK_AMAZON_KEYWORD_QUEUE = 'TaskAmazonKeywordQueue'

# 亚马逊商品详情
TASK_AMAZON_DETAIL_QUEUE = 'TaskAmazonDetailQueue'

# 亚马逊商品评论
TASK_AMAZON_COMMENTS_QUEUE = 'TaskAmazonCommentsQueue'



######################日志配置

LOG_ENABLE = True
LOG_PATH = 'log.log'
