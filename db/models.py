from sqlalchemy import Column, Integer, String, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
from config import Config

Base = declarative_base()

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    address = Column(String(255))
    phone = Column(String(20))
    payment_type = Column(String(20))
    whatsapp_number = Column(String(50))
    items = Column(String(1000))  # JSON string for items
    notes = Column(String(255))
    status = Column(String(20), default='pending')
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Conversation(Base):
    __tablename__ = 'conversations'
    id = Column(Integer, primary_key=True)
    whatsapp_number = Column(String(50))
    sender = Column(String(10))  # 'user' ya 'bot'
    message = Column(String(1000))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

# DB setup
engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def try_init_db():
    try:
        init_db()
        print('Database tables initialized successfully.')
    except Exception as e:
        print('Database initialization error:', e)

try_init_db() 
    
