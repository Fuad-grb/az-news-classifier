from pathlib import Path
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
import time
from typing import List, Optional
import random
import logging

@dataclass
class Article:
    title: str
    url: str
    source: str
    word_count: int = 0
    content: Optional[str] = None
    published_date: Optional[str] = None
    category: Optional[str] = None

class BaseScraper(ABC):
    def __init__(self, storage_path: str = "data/raw", delay: float = 1.5, max_retries: int = 3):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.delay = delay
        self.max_retries = max_retries
        
    @property
    @abstractmethod
    def source_name(self) -> str:
        pass

    @abstractmethod
    def get_article_urls(self, category: str, page: int) -> List[str]:
        pass

    @abstractmethod
    def parse_article(self, url: str, category: str, source: str) -> Optional[Article]:
        pass

    def _get_id(self, url: str) -> str:
        """Extract a unique Slug ID from the article URL"""
        slug = url.strip("/").split("/")[-1]
        if len(slug) > 150:  # Truncate if slug is too long
            slug = slug[:150]
        return f"{self.source_name}_{slug}"

    def save_article(self, article: Article) -> None:
        """Save article to a json file named as its ID"""
        file_id = self._get_id(article.url)
        file_path = self.storage_path / f"{file_id}.json"
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(asdict(article), f, ensure_ascii=False, indent=4)
            
    def scrape_category(self, category: str, max_pages: int):
        """Scrape articles from a specific category and save them"""
        for page in range(1, max_pages + 1):
            article_urls = self.get_article_urls(category, page)
            
            if not article_urls:
                logging.info(f"No more articles found in {category} at page {page}. Stopping.")
                break
            
            new_count = 0
            for url in article_urls:
                if self.is_already_saved(url):
                    logging.info(f"Skipping (already saved): {url}")
                    continue
                
                article = self._safe_parse(url, category)
                if article:
                    self.save_article(article)
                    logging.info(f"Successfully saved: {url}")
                    new_count += 1
                    
                    # Adding a small random delay to avoid hitting the server too hard 
                    time.sleep(self.delay + random.uniform(0, 0.5)) 
            
            logging.info(f"Finished page {page}. Saved {new_count} new articles.")

    def _safe_parse(self, url: str, category: str) -> Optional[Article]:
        """Method to safely parse an article, catching exceptions"""

        for attempt in range(self.max_retries):
            try:
                article = self.parse_article(url, category)
                if article:
                    return article
            except Exception as e:
                logging.error(f"Attempt {attempt + 1} failed for {url}: {e}")
            
            # Exponential backoff 
            wait_time = self.delay * (attempt + 1)
            time.sleep(wait_time)
            
        return None
                    
            
            
    def is_already_saved(self, url: str) -> bool:
        file_id = self._get_id(url)
        return (self.storage_path / f"{file_id}.json").exists()
    
    def scrape_all(self, categories: List[str], max_pages: int):
        logging.info(f"Starting total scraping for categories: {categories} with max pages: {max_pages}")
        for category in categories:
            logging.info(f"Scraping category: {category}")
            self.scrape_category(category, max_pages)
            
        logging.info("Scraping completed.")