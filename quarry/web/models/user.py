from flask import g
import json


class User(object):
    def __init__(self, id, username):
        self.id = id
        self.username = username

    def to_json(self):
        return json.dumps({
            'id': self.id,
            'username': self.username
        })

    @classmethod
    def from_json(cls, json_data):
        data = json.loads(json_data)
        return cls(data['id'], data['username'])

    @staticmethod
    def get_cache_key(id):
        return 'user:id:%s' % (id, )

    @classmethod
    def get_by_id(cls, id):
        user_data = g.redis.get(cls.get_cache_key(id))
        if user_data:
            return User.from_json(user_data)
        try:
            cur = g.conn.cursor()
            cur.execute(
                'SELECT id, username FROM user WHERE id=%s',
                (id, )
            )
            result = cur.fetchone()
        finally:
            cur.close()
        if result is None:
            return None
        user = cls(result[0], result[1])
        g.redis.set(cls.get_cache_key(id), user.to_json())
        return user

    def save(self):
        try:
            cur = g.conn.cursor()
            cur.execute(
                """INSERT INTO user (id, username) VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE username=%s""",
                (self.id, self.username, self.username)
            )
            g.redis.delete(User.get_cache_key(self.id))
        finally:
            cur.close()
