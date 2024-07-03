from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select
from app.models import URL


class URLRepository:
    def __init__(self):
        self.url_cache = set()

    def load_cache(self, session: Session):
        query = select(URL.url)
        result = session.execute(query)
        urls = result.scalars().all()
        self.url_cache = set(urls)

    async def create_url(self, db, url: str):
        if url in self.url_cache:
            return await self.get_url_by_url(db, url)

        try:
            new_url = URL(url=url)
            db.add(new_url)
            await db.commit()
            self.url_cache.add(url)
            return new_url
        except IntegrityError:
            await db.rollback()
            return await self.get_url_by_url(db, url)

    async def get_url_by_url(self, db, url: str):
        query = select(URL).where(URL.url == url)
        result = await db.execute(query)
        return result.scalar_one_or_none()
