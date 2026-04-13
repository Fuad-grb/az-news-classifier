import requests
from bs4 import BeautifulSoup
from .base import BaseScraper, Article
from typing import Optional, List
import logging

class QafqazinfoScraper(BaseScraper):
    @property
    def source_name(self) -> str:
        return "qafqazinfo_az"

    def __init__(self, storage_path="data/raw", delay=0.5, max_retries=3):
        super().__init__(storage_path, delay, max_retries)
        self.base_url = "https://qafqazinfo.az"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def get_article_urls(self, category_path: str, page: int) -> List[str]:
        
        url = f"{self.base_url}/news/category/{category_path}?page={page}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")

            # Looking for links containing '/news/detail/'
            link_tags = soup.select("a[href*='/news/detail/']")
            
            urls = []
            for tag in link_tags:
                href = tag.get("href")
                if href:
                    full_url = href if href.startswith("http") else f"{self.base_url}{href}"
                    urls.append(full_url)
            
            return list(set(urls)) # Return only unique URLs
            
        except Exception as e:
            logging.error(f"Qafqazinfo: Error fetching page {page} for {category_path}: {e}")
            return []

    def parse_article(self, url: str, category: str) -> Optional[Article]:
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")
            

            title_tag = soup.find("title")
            title = title_tag.get_text(strip=True) if title_tag else "No Title"

            content_div = soup.find("div", class_="news_text")
            
            if not content_div:
                return None
                
            paragraphs = content_div.find_all("p")
            content = " ".join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
            
            if not content or len(content) < 50:
                return None

            return Article(
                title=title,
                url=url,
                category=category,
                source=self.source_name,
                word_count=len(content.split()),
                content=content
            )
        except Exception as e:
            logging.error(f"Qafqazinfo: Error parsing article {url}: {e}")
            return None