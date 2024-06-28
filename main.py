from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from . import models, schemas
from database import get_db
from scraper import scrape_url, get_latest_scrape
from datetime import datetime

app = FastAPI()

models.Base.metadata.create_all(bind=engine)


@app.post("/urls/", response_model=schemas.URL)
def create_url(url: schemas.URLCreate, db: Session = Depends(get_db)):
    db_url = models.URL(url=url.url)
    db.add(db_url)
    db.commit()
    db.refresh(db_url)
    return db_url


@app.get("/urls/", response_model=List[schemas.URL])
def read_urls(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    urls = db.query(models.URL).offset(skip).limit(limit).all()
    return urls


@app.post("/scrapes/", response_model=schemas.Scrape)
def create_scrape(scrape: schemas.ScrapeCreate, db: Session = Depends(get_db)):
    db_scrape = models.Scrape(**scrape.dict())
    db.add(db_scrape)
    db.commit()
    db.refresh(db_scrape)
    return db_scrape


@app.get("/scrapes/{url_id}", response_model=List[schemas.Scrape])
def read_scrapes(
    url_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    scrapes = (
        db.query(models.Scrape)
        .filter(models.Scrape.url_id == url_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return scrapes


@app.put("/scrapes/{scrape_id}", response_model=schemas.Scrape)
def update_scrape(
    scrape_id: int, scrape_update: schemas.ScrapeUpdate, db: Session = Depends(get_db)
):
    db_scrape = db.query(models.Scrape).filter(models.Scrape.id == scrape_id).first()
    if db_scrape is None:
        raise HTTPException(status_code=404, detail="Scrape not found")

    update_data = scrape_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_scrape, key, value)

    db.commit()
    db.refresh(db_scrape)
    return db_scrape


@app.post("/changes/", response_model=schemas.Change)
def create_change(
    change: schemas.ChangeBase, scrape_id: int, db: Session = Depends(get_db)
):
    db_change = models.Change(**change.dict(), scrape_id=scrape_id)
    db.add(db_change)
    db.commit()
    db.refresh(db_change)
    return db_change


@app.get("/changes/{scrape_id}", response_model=List[schemas.Change])
def read_changes(scrape_id: int, db: Session = Depends(get_db)):
    changes = db.query(models.Change).filter(models.Change.scrape_id == scrape_id).all()
    return changes


@app.get("/flagged_scrapes/")
async def get_flagged_scrapes():
    query = scrapes.select().where(scrapes.c.create_alert == True)
    return await database.fetch_all(query)


@app.post("/scrape")
async def scrape_endpoint(url: str, db: AsyncSession = Depends(get_db)):
    result = await scrape_url(url, db)
    return result


@app.get("/latest")
async def get_latest_endpoint(url: str, db: AsyncSession = Depends(get_db)):
    result = await get_latest_scrape(url, db)
    if result is None:
        return {"message": "No scrape data found for this URL"}
    return result
