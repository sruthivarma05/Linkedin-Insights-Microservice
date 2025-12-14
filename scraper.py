from scrape_linkedin_company import scrape_company

class Scraper:
    def scrape_page(self, page_url: str):
        return scrape_company(page_url)

scraper = Scraper()
