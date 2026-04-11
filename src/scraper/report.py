import requests
from bs4 import BeautifulSoup
from .base import BaseScraper, Article
from typing import Optional, List
import logging

logging.basicConfig(level=logging.INFO)


class ReportAzScraper(BaseScraper):
    def __init__(self, storage_path = "data/raw"):
        super().__init__(storage_path)
        self.base_url = "https://report.az"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
    def get_article_urls(self, category: str, page: int) -> List[str]:
        url = f"{self.base_url}/{category}/page/{page}"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")
            link_tag = soup.find_all("a", class_="news__item")
            urls = []
            for i in link_tag:
                link = i.get("href")
                if link and link.startswith("/"):
                    urls.append(self.base_url + link)
            logging.info(f"Found {len(urls)} article URLs on page {page} of category '{category}'")
            return urls
        except requests.RequestException as e:
            logging.error(f"Error fetching article URLs: {e}")
            return []
        
    def parse_article(self, url: str) -> Optional[Article]:
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")
            
            title_tag = soup.find("h1", class_= "section-title")
            title = title_tag.text.strip() if title_tag else "No Title"
            
            content_block = soup.find("div", class_= "news-detail__desc")
            content = content_block.get_text(separator=" ", strip=True) if content_block else "No Content"
            
            date_tag = soup.find("ul", class_= "news__date")
            published_date = date_tag.text.strip() if date_tag else "No Date"
            
            return Article(title=title, url=url, content=content, published_date=published_date)
        
        except requests.RequestException as e:
            logging.error(f"Error fetching article content: {e}")
            return None