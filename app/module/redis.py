import redis
from typing import Any, Optional

class RedisClient:
    """Redis 客户端包装"""
    
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0, decode_responses: bool = True):
        """
        初始化 Redis 连接
        
        Args:
            host: Redis 服务器地址
            port: Redis 服务器端口
            db: 数据库编号
            decode_responses: 是否自动解码响应为字符串
        """
        self.client = redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=decode_responses
        )
    
    # ──────── 字符串操作 ────────
    def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """
        设置键值对
        
        Args:
            key: 键名
            value: 值
            ex: 过期时间（秒），None 表示永不过期
        """
        return self.client.set(key, value, ex=ex)
    
    def get(self, key: str) -> Optional[str]:
        """获取键的值"""
        return self.client.get(key)
    
    def delete(self, *keys: str) -> int:
        """删除一个或多个键，返回删除个数"""
        return self.client.delete(*keys)
    
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        return self.client.exists(key) > 0
    
    # ──────── 列表操作 ────────
    def lpush(self, key: str, *values) -> int:
        """从左端插入元素到列表"""
        return self.client.lpush(key, *values)
    
    def rpush(self, key: str, *values) -> int:
        """从右端插入元素到列表"""
        return self.client.rpush(key, *values)
    
    def lpop(self, key: str) -> Optional[str]:
        """从左端弹出元素"""
        return self.client.lpop(key)
    
    def rpop(self, key: str) -> Optional[str]:
        """从右端弹出元素"""
        return self.client.rpop(key)
    
    def lrange(self, key: str, start: int = 0, end: int = -1) -> list:
        """获取列表范围内的元素"""
        return self.client.lrange(key, start, end)
    
    # ──────── 哈希操作 ────────
    def hset(self, key: str, mapping: dict) -> int:
        """设置哈希字段"""
        return self.client.hset(key, mapping=mapping)
    
    def hget(self, key: str, field: str) -> Optional[str]:
        """获取哈希字段值"""
        return self.client.hget(key, field)
    
    def hgetall(self, key: str) -> dict:
        """获取哈希所有字段和值"""
        return self.client.hgetall(key)
    
    def hdel(self, key: str, *fields) -> int:
        """删除哈希字段"""
        return self.client.hdel(key, *fields)
    
    # ──────── 集合操作 ────────
    def sadd(self, key: str, *members) -> int:
        """添加成员到集合"""
        return self.client.sadd(key, *members)
    
    def smembers(self, key: str) -> set:
        """获取集合所有成员"""
        return self.client.smembers(key)
    
    def srem(self, key: str, *members) -> int:
        """从集合移除成员"""
        return self.client.srem(key, *members)
    
    # ──────── 有序集合操作 ────────
    def zadd(self, key: str, mapping: dict) -> int:
        """添加成员到有序集合（mapping: {member: score, ...}）"""
        return self.client.zadd(key, mapping)
    
    def zrange(self, key: str, start: int = 0, end: int = -1) -> list:
        """获取有序集合范围内的成员"""
        return self.client.zrange(key, start, end)
    
    def zrem(self, key: str, *members) -> int:
        """从有序集合移除成员"""
        return self.client.zrem(key, *members)
    
    # ──────── 过期时间操作 ────────
    def expire(self, key: str, seconds: int) -> bool:
        """设置键的过期时间"""
        return self.client.expire(key, seconds)
    
    def ttl(self, key: str) -> int:
        """获取键剩余过期时间（秒），-1 表示永不过期，-2 表示不存在"""
        return self.client.ttl(key)
    
    def ping(self) -> bool:
        """测试连接"""
        return self.client.ping()


# ──────────────────────────────────────
# 使用示例
# ──────────────────────────────────────
if __name__ == "__main__":
    # 初始化
    redis_client = RedisClient(host="localhost", port=6379)
    
    # 连接测试
    if redis_client.ping():
        print("✓ Redis 连接成功")
        
    # 字符串操作
    redis_client.set("user:1:name", "John", ex=3600)  # 设置1小时过期
    print(redis_client.get("user:1:name"))  # 输出: John
    
    # 列表操作
    redis_client.rpush("tasks", "task1", "task2", "task3")
    print(redis_client.lrange("tasks", 0, -1))  # 输出: ['task1', 'task2', 'task3']
    
    # 哈希操作
    redis_client.hset("user:1", {"name": "John", "age": "30", "email": "john@example.com"})
    print(redis_client.hgetall("user:1"))  # 输出: {'name': 'John', 'age': '30', ...}
    
    # 集合操作
    redis_client.sadd("tags", "python", "redis", "database")
    print(redis_client.smembers("tags"))  # 输出: {'python', 'redis', 'database'}
    
    # 有序集合操作
    redis_client.zadd("leaderboard", {"player1": 100, "player2": 95, "player3": 90})
    print(redis_client.zrange("leaderboard", 0, -1))  # 输出: ['player3', 'player2', 'player1']
    