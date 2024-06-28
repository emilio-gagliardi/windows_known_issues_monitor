from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database import Base


class URL(Base):
    __tablename__ = "urls"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, index=True)
    scrapes = relationship("Scrape", back_populates="url")


class Scrape(Base):
    __tablename__ = "scrapes"

    id = Column(Integer, primary_key=True, index=True)
    url_id = Column(Integer, ForeignKey("urls.id"))
    timestamp = Column(DateTime)
    content = Column(String)
    scrape_type = Column(String)  # New field
    scrape_comment = Column(String)  # New field
    create_alert = Column(Boolean, default=False)  # New field
    url = relationship("URL", back_populates="scrapes")
    changes = relationship("Change", back_populates="scrape")


class Change(Base):
    __tablename__ = "changes"

    id = Column(Integer, primary_key=True, index=True)
    scrape_id = Column(Integer, ForeignKey("scrapes.id"))
    change_type = Column(String)
    details = Column(String)
    scrape = relationship("Scrape", back_populates="changes")
