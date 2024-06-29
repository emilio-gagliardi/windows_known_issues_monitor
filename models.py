from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database import Base


class URL(Base):
    __tablename__ = "urls"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, index=True)
    last_scraped = Column(DateTime, nullable=True)
    scrapes = relationship("Scrape", back_populates="url")


class Scrape(Base):
    __tablename__ = "scrapes"

    id = Column(Integer, primary_key=True, index=True)
    url_id = Column(Integer, ForeignKey("urls.id"))
    timestamp = Column(DateTime)
    content = Column(String)
    scrape_type = Column(String)
    scrape_comment = Column(String)
    create_alert = Column(Boolean, default=False)
    url = relationship("URL", back_populates="scrapes")
    changes = relationship("Change", back_populates="scrape")
    hash = Column(String(32), index=True)


class Change(Base):
    __tablename__ = "changes"

    id = Column(Integer, primary_key=True, index=True)
    scrape_id = Column(Integer, ForeignKey("scrapes.id"))
    change_type = Column(String)
    details = Column(String)
    scrape = relationship("Scrape", back_populates="changes")
