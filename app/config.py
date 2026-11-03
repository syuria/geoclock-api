import os


class Config:
    # postgresql+psycopg://user:password@host:port/dbname
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://geoclock:geoclock@localhost:5432/geoclock",
    )
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    TIMESHEET_CACHE_SECONDS = int(os.getenv("TIMESHEET_CACHE_SECONDS", "60"))


class TestConfig(Config):
    TESTING = True
    # Tests use Postgres in CI (DATABASE_URL set) and SQLite locally if not.
    SQLALCHEMY_DATABASE_URI = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")
    SQLALCHEMY_ENGINE_OPTIONS = {}
    # "fake" swaps in an in-memory Redis so tests need no server.
    REDIS_URL = os.getenv("TEST_REDIS_URL", "fake")
