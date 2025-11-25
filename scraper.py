import os
import json
import time
import logging
import argparse
import requests
import re
from datetime import datetime
from urllib.parse import urljoin, urlencode

from utils import (prepare_payload, 
                   process_documents, 
                   setup_session)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s: %(message)s",
    handlers=[logging.FileHandler("output/scraper.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

with open("config.json", "r") as f:
    config_data = json.load(f)

# --------------------------
# Main scraper logic
# --------------------------


def scrape_decisions(date):

    dt = datetime.strptime(date, "%Y-%m-%d")
    session = setup_session(config_data, logger)
    logger.info(f"Starting search for decisions up to {dt.date()}")

    # Send search request
    try:
        payload = prepare_payload(dt)
        response = session.post(
            urljoin(
                config_data.get("base_url"), 
                config_data.get("search_path")), 
            json=payload, timeout=30
        )
        response.raise_for_status()
        logger.info(f"Search request successful (status {response.status_code})")
    except requests.RequestException as e:
        logger.error(f"Search request failed: {e}")
        return

    # Parse JSON
    try:
        results_json = response.json()
    except json.JSONDecodeError:
        logger.error("Response is not JSON as expected")
        return

    documents = results_json.get("data", [])
    logger.debug(f"Found {len(documents)} documents in search results")
    if not documents:
        logger.info("No decisions found in response")
        return

    documents_dir = os.path.join(config_data.get("output_dir"), "documents")
    os.makedirs(documents_dir, exist_ok=True)

    document_list = process_documents(session, documents, logger, config_data)

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

    os.makedirs(config_data.get("output_dir"), exist_ok=True)
    with open(
        os.path.join(config_data.get("output_dir"), "metadata.json"), "w", encoding="utf-8"
    ) as metafile:
        json.dump(metadata, metafile, ensure_ascii=False, indent=2)

    with open(
        os.path.join(config_data.get("output_dir"), "download_log.txt"), "w", encoding="utf-8"
    ) as logf:
        for doc in document_list:
            logf.write(f"{doc['filename']} - {doc['download_status']}\n")

    logger.info(
        f"Scraping complete: {metadata['successful_downloads']} successful, {metadata['failed_downloads']} failed."
    )

def main():
    parser = argparse.ArgumentParser(
        description="Israeli Supreme Court Decision Scraper"
    )
    parser.add_argument("--date", required=True, help="Search date YYYY-MM-DD")
    parser.add_argument("--output-dir", default="output", help="Output directory path")
    args = parser.parse_args()

    scrape_decisions(date=args.date)


if __name__ == "__main__":
    main()
