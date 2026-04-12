import requests
from bs4 import BeautifulSoup
from .base import BaseScraper, Article
from typing import Optional, List
import logging

class SonxeberScraper(BaseScraper):
    @property
    def source_name(self) -> str:
        return "sonxeber_az"

    def __init__(self, storage_path="data/raw", delay=1.5, max_retries=3):
        super().__init__(storage_path, delay, max_retries)
        self.base_url = "https://sonxeber.az"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def get_article_urls(self, category: str, page: int) -> List[str]:
        # Param 'start' is calculated based on page number, Sonxeber contains 30 articles per page
        start_val = (page - 1) * 30 + 1
        url = f"{self.base_url}/{category}/?start={start_val}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")
            

            link_tags = soup.find_all("a", class_="thumb_zoom")
            
            logging.info(f"Sonxeber: Found {len(link_tags)} article link tags on page {page} of category '{category}'")
            
            urls = []
            for tag in link_tags:
                href = tag.get("href")
                if href: # Filtering only article links
                    clean_href = href.lstrip('/')
                    if clean_href and clean_href[0].isdigit():
                        full_url = f"{self.base_url}/{clean_href}"
                        urls.append(full_url)
            
            # Cleaning and deduplicating URLs
            unique_urls = list(set(urls))
            logging.info(f"Sonxeber: Found {len(unique_urls)} unique URLs on page {page}")
            
            if not unique_urls and link_tags:
                 logging.info(f"DEBUG: First found href was: {link_tags[0].get('href')}")
            
            return unique_urls
            
        except Exception as e:
            logging.error(f"Sonxeber: Error fetching URLs from {url}: {e}")
            return []

    def parse_article(self, url: str, category: str) -> Optional[Article]:
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")
            
            # Article text is inside <article> tag
            article_container = soup.find("article")
            
            if not article_container:
                logging.warning(f"Sonxeber: Could not find <article> tag at {url}")
                return None
            
            title_tag = article_container.find("h1")
            title = title_tag.get_text(strip=True) if title_tag else "No Title"
            
            # Extracting content from all <p> tags within the article container
            
            paragraphs = article_container.find_all("p")
            content = " ".join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
            
            date_div = soup.find("div", class_="datespan")
            
            if date_div:
                raw_date_text = date_div.get_text(strip=True)
                # The date text contains İqtisadiyyat   Baxılıb: 270   Tarix: 08 aprel 2026   
                published_date = raw_date_text.split("Tarix:")[-1].strip() if "Tarix:" in raw_date_text else raw_date_text
            else:
                published_date = None

            return Article(
                title=title,
                url=url,
                category=category,
                source=self.source_name,
                word_count=len(content.split()),
                content=content,
                published_date=published_date
            )
        except Exception as e:
            logging.error(f"Sonxeber: Error parsing article {url}: {e}")
            return None