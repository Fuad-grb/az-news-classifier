from pathlib import Path
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import List, Optional

@dataclass
class Article:
    title: str
    url: str
    content: Optional[str] = None
    published_date: Optional[str] = None
    category: Optional[str] = None

class BaseScraper(ABC):
    def __init__(self, storage_path: str = "data/raw"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    
    def get_article_urls(self, category: str, page: int) -> List[str]:
        pass

    @abstractmethod
    def parse_article(self, url: str) -> Optional[Article]:
        pass

    def _get_id(self, url: str) -> str:
        """Extract a unique Slug ID from the article URL"""
        return url.strip("/").split("/")[-1]

    def is_already_saved(self, url: str) -> bool:
        file_id = self._get_id(url)
        return (self.storage_path / f"{file_id}.json").exists()

    def save_article(self, article: Article) -> None:
        """Save article to a json file named as its ID"""
        file_id = self._get_id(article.url)
        file_path = self.storage_path / f"{file_id}.json"
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(asdict(article), f, ensure_ascii=False, indent=4)