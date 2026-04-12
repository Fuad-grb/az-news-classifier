import logging
from src.scraper.qafqazinfo import QafqazinfoScraper
from src.scraper.sonxeber import SonxeberScraper
from src.scraper.report import ReportAzScraper

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    scrapers = [
        QafqazinfoScraper(delay=0.7)
        #SonxeberScraper(delay=1.5),
        #ReportAzScraper(delay=1.5)
    ]
    
    for scraper in scrapers:
        logging.info(f"Starting scraping for {scraper.source_name}")
        if scraper.source_name == "sonxeber_az":
            target_categories = [
                "iqtisadiyyat-xeberleri",
                "siyaset-xeberleri",
                "sosial-xeberler",
                "idman-xeberleri",
                "medeniyyet-xeberleri",
                "dunya-xeberleri"
            ]
        elif scraper.source_name == "report_az":
            target_categories = [
                "siyasi-xeberler",
                "iqtisadiyyat-xeberleri",
                "cemiyyet",
                "idman-xeberleri",
                "medeniyyet-xeberleri",
                "dunya-xeberleri"
            ]
            
        elif scraper.source_name == "qafqazinfo_az":
            target_categories = [
                "idman-9",
                "dunya-6",
                "siyaset-2"
            ]
    
    
        scraper.scrape_all(
            categories=target_categories,
            max_pages=70
        )

if __name__ == "__main__":
    main()