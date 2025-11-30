# web-scraping

## Israeli Supreme Court – Decision Scraper

A Python tool that scrapes and downloads decision documents (PDF/DOCX) from the
Israeli Supreme Court website using **HTTP requests only**.

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

## Project Structure

**1. `scripts/`**

* **`prepare_search.py`** – Prepare the payload using the intput from command line and peform search.
* **`process_download.py`** – Peforms extraction, sanitization and saving the documents and meta data.
* **`utility_functions.py`** – Contains functions that are used for session, logger, and config setup.

**2. `scraper.py`** - Runs the entire pipeline end-to-end, including searching, processing, and downloading.

**3. `output/`** - Stores all downloaded documents, meta data, and logs.

## Installation

```bash
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python ./scraper.py --start_date 2012-10-10 --end_date 2015-11-24 --output-dir ./output
python ./scraper.py --start_date 2012-10-10 --end_date 2015-11-24 --case_type 1 2 --output-dir ./output 
python ./scraper.py --start_date 2012-10-10 --end_date 2015-11-24 --decision_type 1 2 --output-dir ./output 
python ./scraper.py --start_date 2012-10-10 --end_date 2015-11-24  --keywords "Israel" --output-dir ./output 
```
