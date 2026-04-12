import requests
from bs4 import BeautifulSoup
from .base import BaseScraper, Article
from typing import Optional, List
import logging

logging.basicConfig(level=logging.INFO)


class ReportAzScraper(BaseScraper):
    
    @property
    def source_name(self) -> str:
        return "report.az"
    
    def __init__(self, storage_path = "data/raw", delay: float = 1.5, max_retries: int = 3):
        super().__init__(storage_path = storage_path, delay = delay, max_retries = max_retries)
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
        
    def parse_article(self, url: str, category: str) -> Optional[Article]:
        try:
            response = requests.get(url, headers=self.headers)
            response.encoding = 'utf-8'
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")
            
            title_tag = soup.find("h1", class_= "section-title")
            title = title_tag.text.strip() if title_tag else "No Title"
            
            content_block = soup.find("div", class_= "news-detail__desc")
            content = content_block.get_text(separator=" ", strip=True) if content_block else "No Content"
            
            word_count = len(content.split())
            
            date_tag = soup.find("ul", class_= "news__date")
            published_date = date_tag.text.strip() if date_tag else "No Date"
            published_date = published_date.replace(" ", "").replace("\n", "")
            published_date = " ".join(published_date.split())
            
            return Article(title=title, url=url, source=self.source_name, word_count=word_count, content=content, published_date=published_date, category=category)
        
        except requests.RequestException as e:
            logging.error(f"Error fetching article content: {e}")
            return None