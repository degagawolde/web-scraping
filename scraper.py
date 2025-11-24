import os
import re
import json
import time
import logging
import argparse
import requests
from datetime import datetime
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Set up logging configuration
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s: %(message)s",
    handlers=[logging.FileHandler("scraper.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def sanitize_filename(s):
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"\s+", "_", s)
    return s.lower()


def setup_session():
    session = requests.Session()
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/116.0.0.0 Safari/537.36"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;"
            "q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }
    session.headers.update(headers)

    retries = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    logger.debug("HTTP session initialized with retries and headers")
    return session


def download_file(session, url, dest_path):
    logger.debug(f"Starting download from {url}")
    try:
        resp = session.get(url, stream=True, timeout=20)
        resp.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        size = os.path.getsize(dest_path)
        logger.info(f"Downloaded file saved to {dest_path} (size: {size} bytes)")
        return True, size
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        return False, 0


def scrape_decisions(date, output_dir="output"):
    base_url = "https://supreme.court.gov.il"
    search_path = "/sites/en/Pages/SearchJudgments.aspx"

    dt = datetime.strptime(date, "%Y-%m-%d")
    year = dt.year
    month = dt.month

    params = {
        "OpenYearDate": year,
        "CaseNumber": "null",
        "DateType": 1,
        "SearchPeriod": 20,
        "COpenDate": "null",  # Use explicit date range
        "CEndDate": "null",
        "freeText": "null",
        "Importance": "null",
        "CaseMonth": month,
    }

    session = setup_session()
    logger.info(f"Starting search for decisions on {dt}")

    try:
        resp = session.get(urljoin(base_url, search_path), params=params, timeout=30)
        resp.raise_for_status()
        logger.info("Search request successful")
    except requests.RequestException as e:
        logger.error(f"Search request failed: {e}")
        return

    soup = BeautifulSoup(resp.text, "html.parser")

    # Find results container
    results_container = soup.find("div", class_="results-listing")
    if not results_container:
        logger.warning("Results container not found; check site structure or params")
        return

    decision_items = results_container.find_all("li", recursive=False)
    if not decision_items:
        logger.info("No decisions found for the specified date")
        return

    documents_dir = os.path.join(output_dir, "documents")
    os.makedirs(documents_dir, exist_ok=True)

    document_list = []
    sequential = 1

    for item in decision_items:
        try:
            case_number = item.select_one("div.res-link > a").get_text(strip=True)
            parties = item.select_one("div.res-title > p").get_text(strip=True)
            decision_date = item.select_one("span.res-date").get_text(strip=True)
            doc_type_label = item.select_one("span.res-type").get_text(strip=True)

            # Find PDF or DOC link:
            pdf_link_tag = item.select_one("a.file-link.pdf-link")
            doc_link_tag = item.select_one("a.file-link.doc-link")

            if pdf_link_tag:
                doc_url = urljoin(base_url, pdf_link_tag["href"])
                doc_type = "pdf"
            elif doc_link_tag:
                doc_url = urljoin(base_url, doc_link_tag["href"])
                doc_type = "docx"
            else:
                logger.warning(
                    f"No document link found for case {case_number}, skipping"
                )
                continue

            filename_safe = sanitize_filename(
                f"{case_number}_{date}_{sequential:03d}.{doc_type}"
            )
            filepath = os.path.join(documents_dir, filename_safe)

            logger.info(f"Downloading {filename_safe} from {doc_url}")
            success, filesz = download_file(session, doc_url, filepath)
            status = "success" if success else "failed"

            document_list.append(
                {
                    "case_number": case_number,
                    "decision_date": decision_date,
                    "parties": parties,
                    "document_type": doc_type,
                    "file_size_bytes": filesz,
                    "filename": filename_safe,
                    "download_url": doc_url,
                    "download_status": status,
                }
            )

            sequential += 1
            time.sleep(1)  # Be polite and avoid hammering the server

        except Exception as e:
            logger.error(f"Error parsing or downloading decision: {e}")
            continue

    metadata = {
        "search_date": date,
        "download_timestamp": datetime.now().isoformat(),
        "total_documents": len(document_list),
        "successful_downloads": sum(
            d["download_status"] == "success" for d in document_list
        ),
        "failed_downloads": sum(
            d["download_status"] == "failed" for d in document_list
        ),
        "documents": document_list,
    }

    with open(os.path.join(output_dir, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    with open(os.path.join(output_dir, "download_log.txt"), "w", encoding="utf-8") as f:
        for doc in document_list:
            f.write(f"{doc['filename']} - {doc['download_status']}\n")

    logger.info(
        f"Scraping complete. {metadata['successful_downloads']} files downloaded successfully."
    )


def main():
    parser = argparse.ArgumentParser(
        description="Israeli Supreme Court Decision Scraper"
    )
    parser.add_argument("--date", required=True, help="Search date YYYY-MM-DD")
    parser.add_argument("--output-dir", default="output", help="Output directory path")
    args = parser.parse_args()

    scrape_decisions(date=args.date, output_dir=args.output_dir)


if __name__ == "__main__":
    main()
