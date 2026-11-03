from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
migrate = Migrate()


def init_redis(app):
    """Attach a Redis client to the app as app.extensions['redis']."""
    url = app.config["REDIS_URL"]
    if url == "fake":
        import fakeredis
        client = fakeredis.FakeRedis(decode_responses=True)
    else:
        import redis
        client = redis.Redis.from_url(url, decode_responses=True)
    app.extensions["redis"] = client
