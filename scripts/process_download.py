import datetime
import json
import os
import re
import time
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlencode

import requests
from traitlets import Any


def download_file(
    session: requests.Session, url: str, dest_path: str, logger
) -> Tuple[bool, int]:
    """Download file from URL to destination path."""
    logger.debug(f"Starting download from {url}")
    try:
        response = session.get(url, stream=True, timeout=20)
        response.raise_for_status()

        with open(dest_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)

        file_size = os.path.getsize(dest_path)
        logger.info(f"Downloaded file saved to {dest_path} (size: {file_size} bytes)")
        return True, file_size

    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        return False, 0


def get_file_extension(file_type: int) -> str:
    """Determine file extension based on type code."""
    extension_map = {2: "pdf", 4: "pdf", 3: "docx"}
    return extension_map.get(file_type, "txt")


def sanitize_filename(filename: str) -> str:
    """Sanitize filename by removing special characters and normalizing spaces."""
    filename = re.sub(r"[^\w\s-]", "", filename)
    filename = re.sub(r"\s+", "_", filename)
    return filename.lower()


def parse_ms_date(ms_date: str) -> str:
    """Convert /Date(165000000000)/ to YYYY-MM-DD format."""
    if not ms_date:
        return ""

    match = re.search(r"/Date\((\d+)\)/", ms_date)
    if not match:
        return ""

    timestamp = int(match.group(1)) / 1000
    return datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d")


def process_documents(
    session: requests.Session, documents: List[Dict], logger, config: Dict[str, Any]
) -> List[Dict]:
    """Process and download documents from search results."""
    processed_docs = []

    for index, document in enumerate(documents, 1):
        try:
            result = _process_single_document(session, document, index, logger, config)
            if result:
                processed_docs.append(result)
                time.sleep(1)  # Rate limiting

        except Exception as e:
            logger.error(f"Error processing document {index}: {e}")
            continue

    return processed_docs


def build_download_url(base_url: str, path: str, filename: str, file_type: int) -> str:
    """Build download URL from components."""
    params = {"path": path, "fileName": filename, "type": file_type}
    return f"{base_url}/Home/Download?{urlencode(params)}"


def _process_single_document(
    session: requests.Session,
    document: Dict,
    index: int,
    logger,
    config: Dict[str, Any],
) -> Optional[Dict]:
    """Process a single document and return metadata."""
    case_number = document.get("CaseNum", f"case_{index}")
    ms_date = document.get("VerdictDt")
    decision_date = parse_ms_date(ms_date)
    case_name = document.get("CaseName", "")

    path = document.get("PathForWeb")
    filename = document.get("FileName")
    file_type = document.get("TypeCode")

    if not path or not filename:
        logger.warning(f"Missing path or filename for case {case_number}, skipping")
        return None

    extension = get_file_extension(file_type)
    if extension not in ("pdf", "docx"):
        logger.info(
            f"Skipping unsupported file type '{file_type}' for case {case_number}"
        )
        return None

    download_url = build_download_url(config["base_url"], path, filename, file_type)
    safe_filename = sanitize_filename(f"{case_number}_{decision_date}_{index:04d}")
    filepath = os.path.join(config["output_dir"], f"{safe_filename}.{extension}")

    logger.info(f"Downloading {safe_filename} from {download_url}")
    success, file_size = download_file(session, download_url, filepath, logger)

    return {
        "case_number": case_number,
        "decision_date": decision_date,
        "parties": case_name,
        "document_type": extension,
        "file_size_bytes": file_size,
        "filename": safe_filename,
        "download_url": download_url,
        "download_status": "success" if success else "failed",
    }


def save_metadata(
    documents: list, config: dict, start_date: str, end_date: str, logger
):
    """Save download metadata to JSON file."""
    successful_downloads = sum(doc["download_status"] == "success" for doc in documents)
    failed_downloads = sum(doc["download_status"] == "failed" for doc in documents)

    metadata = {
        "start_date": start_date,
        "end_date": end_date,
        "download_timestamp": datetime.now().isoformat(),
        "total_documents": len(documents),
        "successful_downloads": successful_downloads,
        "failed_downloads": failed_downloads,
        "documents": documents,
    }

    metadata_path = os.path.join(config["output_dir"], "metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as metadata_file:
        json.dump(metadata, metadata_file, ensure_ascii=False, indent=2)

    # Save download log
    log_path = os.path.join(config["output_dir"], "download_log.txt")
    with open(log_path, "w", encoding="utf-8") as log_file:
        for doc in documents:
            log_file.write(f"{doc['filename']} - {doc['download_status']}\n")

    logger.info(
        f"Scraping complete: {successful_downloads} successful, {failed_downloads} failed"
    )
