from database import Base
from sqlalchemy import Column, Integer, String, TIMESTAMP,ForeignKey
from sqlalchemy.sql.expression import text

class Users(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, nullable=False)
    email = Column(String, nullable=False, unique=True)
    hashed_password = Column(String, nullable=False)
    api_key = Column(String, nullable=False, unique=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

class URLS(Base):
    __tablename__ = "urls"
    id = Column(Integer, primary_key=True, nullable=False)
    short_code = Column(String, nullable=False, unique=True)
    original_url = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id",ondelete="CASCADE"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    expires_at = Column(TIMESTAMP(timezone=True), nullable=True)

class Clicks(Base):
    __tablename__ = "clicks"
    id = Column(Integer, primary_key=True, nullable=False)
    url_id = Column(Integer, ForeignKey("urls.id",ondelete="CASCADE"), nullable=False)
    clicked_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)

