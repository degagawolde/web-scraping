import argparse
from datetime import datetime
import os
from typing import List

from scripts.process_download import process_documents, save_metadata
from scripts.prepare_search import search_documents
from scripts.utility_functions import load_config, setup_logging, setup_session

def scrape_decisions(
        start_date: str, 
        end_date: str,
        decision_type:List[int],
        case_type:list[int], 
        keywords:str,
        output_dir: str):

    """
    Scrape Supreme Court decisions between start_date and end_date.

    Parameters:
        start_date (str): Search start date in YYYY-MM-DD format
        end_date (str): Search end date in YYYY-MM-DD format
        decision_type (List[int]): List of decision type codes
        case_type (List[int]): List of case type codes
        output_dir (str): Directory to save downloaded documents
        keywords (str): Search text
    """
    config = load_config()
    config["output_dir"] = output_dir  # Override output directory

    logger = setup_logging(output_dir)
    session = setup_session(config, logger)

    # Create documents subdirectory
    documents_dir = os.path.join(output_dir, "documents")
    os.makedirs(documents_dir, exist_ok=True)
    config["documents_dir"] = documents_dir  # Update for document downloads

    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")
    documents = search_documents(
        session,
        config,
        start_date,
        end_date,
        decision_type,
        case_type,
        keywords,
        logger
    )

    if not documents:
        logger.info("No documents found for the specified criteria")
        return

    processed_documents = process_documents(session, documents, logger, config)
    save_metadata(
        processed_documents,
        config,
        start_date.strftime("%Y-%m-%d"),
        end_date.strftime("%Y-%m-%d"),
        logger
    )


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Israeli Supreme Court Decision Scraper"
    )

    # Date arguments
    parser.add_argument(
        "--start_date", required=True, help="Search start date in YYYY-MM-DD format"
    )
    parser.add_argument(
        "--end_date", required=True, help="Search end date in YYYY-MM-DD format"
    )

    # Output directory
    parser.add_argument("--output-dir", default="output", help="Output directory path")

    # ----- New: Decision type & Case type -----
    parser.add_argument(
        "--decision_type",
        nargs="+",  # allows multiple values
        type=int,
        required=False,
        help="Decision type(s). 1=Decision, 2=Judgment",
    )
    # keywords for text search
    parser.add_argument("--keywords", default="", help="Search Text")
    parser.add_argument(
        "--case_type",
        nargs="+",  # allows multiple values
        type=int,
        required=False,
        help="Case type(s). e.g., 13=CrimA, 21=ADA, etc.",
    )

    args = parser.parse_args()

    # Call scraper with parsed arguments
    scrape_decisions(
        start_date=args.start_date,
        end_date=args.end_date,
        output_dir=args.output_dir,
        decision_type=args.decision_type or [],  # empty list if not provided
        case_type=args.case_type or [],  # empty list if not provided
        keywords=args.keywords or []
    )


if __name__ == "__main__":
    main()
