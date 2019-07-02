import redis
from config import ENV


host = 'redis' if ENV == 'PROD' else '127.0.0.1'
red = redis.Redis(host=host, port=6379)
