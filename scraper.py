import argparse
import datetime
import os

from scripts.process_download import process_documents, save_metadata
from scripts.prepare_search import search_documents
from utils import load_config, setup_logging, setup_session

def scrape_decisions(start_date: str, end_date: str, output_dir: str):
    """Main function to scrape decisions for a given date."""
    config = load_config()
    config["output_dir"] = output_dir  # Override output directory

    logger = setup_logging(output_dir)
    session = setup_session(config, logger)

    # Create documents subdirectory
    documents_dir = os.path.join(output_dir, "documents")
    os.makedirs(documents_dir, exist_ok=True)
    config["output_dir"] = documents_dir  # Update for document downloads

    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")
    documents = search_documents(session, config, start_date, end_date, logger)

    if not documents:
        logger.info("No documents found for the specified criteria")
        return

    processed_documents = process_documents(session, documents, logger, config)
    save_metadata(processed_documents, config, start_date, end_date, logger)


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Israeli Supreme Court Decision Scraper"
    )
    parser.add_argument(
        "--start_date", required=True, help="Search date in YYYY-MM-DD format"
    )
    parser.add_argument(
        "--end_date", required=True, help="Search date in YYYY-MM-DD format"
    )
    parser.add_argument("--output-dir", default="output", help="Output directory path")

    args = parser.parse_args()
    scrape_decisions(args.start_date, args.end_date, args.output_dir)


if __name__ == "__main__":
    main()
