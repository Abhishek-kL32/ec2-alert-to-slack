import redis

# Redis configuration
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0

# Initialize Redis client
redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

# List all keys in Redis
keys = redis_client.keys('*')

# Print each key with its TTL (Time to Live)
for key in keys:
    ttl = redis_client.ttl(key)
    print(f'Task ID: {key.decode()}, TTL: {ttl} seconds')

