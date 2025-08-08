import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SQLITE_PATH = os.path.join(APP_ROOT, 'data', 'app.db')
os.makedirs(os.path.dirname(DEFAULT_SQLITE_PATH), exist_ok=True)

# Prefer DATABASE_URL from env (e.g., Postgres on Supabase/Railway). Fallback to local SQLite.
_raw_url = os.environ.get('DATABASE_URL', f'sqlite:///{DEFAULT_SQLITE_PATH}')

# Normalize Postgres schemes for SQLAlchemy psycopg3 driver
if _raw_url.startswith('postgres://'):
    DATABASE_URL = _raw_url.replace('postgres://', 'postgresql+psycopg://', 1)
elif _raw_url.startswith('postgresql://') and '+psycopg' not in _raw_url:
    DATABASE_URL = _raw_url.replace('postgresql://', 'postgresql+psycopg://', 1)
else:
    DATABASE_URL = _raw_url

engine_kwargs = {"future": True, "pool_pre_ping": True}
connect_args = {}
if DATABASE_URL.startswith('sqlite:///'):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)
Base = declarative_base()