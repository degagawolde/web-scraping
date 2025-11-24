import os
import re
import json
import argparse
import requests
from datetime import datetime
from urllib.parse import urljoin
from bs4 import BeautifulSoup

def sanitize_filename(s):
    # Convert Hebrew chars to Latin or remove unsafe chars
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'\s+', '_', s)
    return s.lower()

def download_file(session, url, dest_path):
    response = session.get(url, stream=True)
    if response.status_code == 200:
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        return True, os.path.getsize(dest_path)
    return False, 0

def scrape_decisions(date, decision_type=None, case_type=None, keywords=None, output_dir='output'):
    base_url = "https://supreme.court.gov.il/"
    search_url = urljoin(base_url, "search_path_placeholder")  # Replace with actual search path
    
    session = requests.Session()

    # Prepare search payload (to be adapted to the real form fields)
    payload = {
        "start_date": date,
        "end_date": date,
    }
    if decision_type:
        payload["decision_type"] = decision_type
    if case_type:
        payload["case_type"] = case_type
    if keywords:
        payload["keywords"] = keywords

    # Send search POST or GET request
    resp = session.post(search_url, data=payload)  # Or .get() if the form uses GET
    soup = BeautifulSoup(resp.text, 'html.parser')

    # Parse results page for cases and document links
    document_list = []
    documents_dir = os.path.join(output_dir, "documents")
    os.makedirs(documents_dir, exist_ok=True)

    # Example parse logic: Find all rows or divs containing decisions
    cases = soup.find_all('div', class_='case-row')  # Adjust selector as needed

    sequential = 1
    for case in cases:
        # Extract metadata
        case_number = case.find('span', class_='case-number').text.strip()
        decision_date = date
        parties = case.find('span', class_='case-parties').text.strip()
        file_link = case.find('a', href=True)['href']
        doc_url = urljoin(base_url, file_link)
        doc_type = 'pdf' if doc_url.lower().endswith('.pdf') else 'docx'
        
        # Generate filename
        filename = f"case_{sequential:03d}_{date}.{doc_type}"
        filepath = os.path.join(documents_dir, filename)

        # Download the file
        success, size = download_file(session, doc_url, filepath)
        status = "success" if success else "failed"

        document_list.append({
            "case_number": case_number,
            "decision_date": decision_date,
            "parties": parties,
            "document_type": doc_type,
            "file_size_bytes": size,
            "filename": filename,
            "download_url": doc_url,
            "download_status": status
        })

        sequential += 1

    # Create metadata JSON
    metadata = {
        "search_date": date,
        "download_timestamp": datetime.now().isoformat(),
        "total_documents": len(document_list),
        "successful_downloads": sum(1 for d in document_list if d["download_status"] == "success"),
        "failed_downloads": sum(1 for d in document_list if d["download_status"] == "failed"),
        "documents": document_list
    }

    with open(os.path.join(output_dir, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    with open(os.path.join(output_dir, "download_log.txt"), "w", encoding="utf-8") as log_file:
        for doc in document_list:
            log_file.write(f"{doc['filename']} - {doc['download_status']}\n")

def main():
    parser = argparse.ArgumentParser(description="Israeli Supreme Court Decision Scraper")
    parser.add_argument("--date", required=True, help="Date to search (YYYY-MM-DD)")
    parser.add_argument("--decision-type", help="Decision type filter")
    parser.add_argument("--case-type", help="Case type filter")
    parser.add_argument("--keywords", help="Keywords filter")
    parser.add_argument("--output-dir", default="output", help="Output directory")
    args = parser.parse_args()

    scrape_decisions(
        date=args.date,
        decision_type=args.decision_type,
        case_type=args.case_type,
        keywords=args.keywords,
        output_dir=args.output_dir
    )

if __name__ == "__main__":
    main()
