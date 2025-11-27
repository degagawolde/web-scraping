# web-scraping

## Israeli Supreme Court – Decision Scraper

A Python tool that scrapes and downloads decision documents (PDF/DOCX) from the
Israeli Supreme Court website for a **single day** using **HTTP requests only**.

---

## Features

- Search by **date**, **decision type**, **case type**, **keywords**
- Download all available **PDF/DOCX** decision files
- Extract metadata:
  - Case number
  - Parties
  - Decision date
  - File size
  - Document type
  - Download URL
- Save documents with a clean naming format
- Produce:
  - `documents/` folder with all files
  - `metadata.json`
  - `download_log.txt`

---

## Installation

```bash
pip install -r requirements.txt
```

## Run

```bash
python ./scraper.py --start_date 2012-10-10 --end_date 2015-11-24 --output-dir ./output
python ./scraper.py --start_date 2012-10-10 --end_date 2015-11-24 --case_type 1 2 --output-dir ./output 
python ./scraper.py --start_date 2012-10-10 --end_date 2015-11-24 --decision_type 1 2 --output-dir ./output 
python ./scraper.py --start_date 2012-10-10 --end_date 2015-11-24  --keywords "Israel" --output-dir ./output 
```
