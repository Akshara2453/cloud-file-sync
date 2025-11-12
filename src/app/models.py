from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base
import datetime

Base = declarative_base()

class FileMetadata(Base):
    __tablename__ = "file_metadata"
    id = Column(Integer, primary_key=True, index=True)
    # MySQL requires a length for VARCHAR, so specify a size.
    filename = Column(String(255), nullable=False, index=True)
    s3_key = Column(String(1024), nullable=False, unique=True, index=True)
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)
    version = Column(Integer, default=1)