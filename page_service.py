from app.utils.db import db
from app.services.scraper import scraper

class PageService:

    def get_page(self, page_id: str):
        """Return page from DB; if not found, scrape and insert."""
        page = db.pages.find_one({"page_id": page_id})

        if page:
            page["_id"] = str(page["_id"])
            return page
        
        scraped = scraper.scrape_page(page_id)

        if "error" in scraped:
            return scraped
        
        db.pages.insert_one(scraped)
        return scraped


    def filter_pages(self, min_followers=None, max_followers=None, name=None, industry=None):
        """Apply various filters on pages."""
        query = {}

        if min_followers and max_followers:
            query["followers"] = {"$gte": min_followers, "$lte": max_followers}

        if name:
            query["name"] = {"$regex": name, "$options": "i"}

        if industry:
            query["industry"] = industry

        results = list(db.pages.find(query))

        for r in results:
            r["_id"] = str(r["_id"])
        
        return results


page_service = PageService()
