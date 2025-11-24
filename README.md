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
