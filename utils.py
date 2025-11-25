from datetime import datetime
import os
import re
import time
from urllib.parse import urlencode

import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry


def sanitize_filename(s):
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"\s+", "_", s)
    return s.lower()


def setup_session(config_data, logger):
    session = requests.Session()
    session.headers.update(config_data.get("headers", {}))
    session.cookies.update(config_data.get("cookies", {}))

    retries = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "POST", "GET", "OPTIONS"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    logger.debug("HTTP session initialized with retries, headers, and cookies")
    return session


def download_file(session, url, dest_path, logger):
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


def parse_ms_date(ms_date: str) -> str:
    """Convert /Date(165000000000)/ → YYYY-MM-DD."""
    if not ms_date:
        return ""
    match = re.search(r"/Date\((\d+)\)/", ms_date)
    if not match:
        return ""
    ts = int(match.group(1)) / 1000
    return datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d")


def build_download_url(base_url: str, path: str, file_name: str, type_code: int) -> str:
    """
    Converts fields into the official document-download endpoint.
    Example final URL:
    https://supremedecisions.court.gov.il/Home/Download?path=EnglishVerdicts/20/440/021/v26&fileName=20021440.V26&type=4
    """
    params = {
        "path": path,
        "fileName": file_name,
        "type": type_code,
    }
    return f"{base_url}/Home/Download?{urlencode(params)}"


def determine_ext(type_code):
    if type_code==4 or type_code==2:
        return "pdf"
    if type_code==3:
        return "docx"
    return "txt"


def prepare_payload(dt):

    data = {
        "document": {
            "Year": None,
            "Month": None,
            "CaseNum": None,
            "Technical": None,
            "fromPages": None,
            "toPages": None,
            "dateType": 2,
            "PublishFrom": "1990-11-23T21:00:00.000Z",
            "PublishTo": dt.isoformat() + "Z",
            "publishDate": 8,
            "translationDateType": 1,
            "translationPublishFrom": "2025-10-24T17:21:39.185Z",
            "translationPublishTo": "2025-11-24T17:21:39.185Z",
            "translationPublishDate": 8,
            "SearchText": [
                {
                    "Text": "",
                    "textOperator": 1,
                    "option": "2",
                    "Inverted": False,
                    "Synonym": False,
                    "NearDistance": 3,
                    "MatchOrder": False,
                }
            ],
            "Judges": None,
            "Parties": [
                {
                    "Text": "",
                    "textOperator": 2,
                    "option": "2",
                    "Inverted": False,
                    "Synonym": False,
                    "NearDistance": 3,
                    "MatchOrder": False,
                }
            ],
            "Counsel": [
                {
                    "Text": "",
                    "textOperator": 2,
                    "option": "2",
                    "Inverted": False,
                    "Synonym": False,
                    "NearDistance": 3,
                    "MatchOrder": False,
                }
            ],
            "Mador": None,
            "CodeMador": [],
            "TypeCourts": None,
            "TypeCourts1": None,
            "TerrestrialCourts": None,
            "LastInyan": None,
            "LastCourtsYear": None,
            "LastCourtsMonth": None,
            "LastCourtCaseNum": None,
            "Old": False,
            "JudgesOperator": 2,
            "Judgment": None,
            "Type": None,
            "CodeTypes": [],
            "CodeJudges": [],
            "Inyan": None,
            "CodeInyan": [],
            "AllSubjects": [
                {"Subject": None, "SubSubject": None, "SubSubSubject": None}
            ],
            "CodeSub2": [],
            "Category1": None,
            "Category3": None,
            "CodeCategory3": [],
            "OldMainNumFormat": False,
            "Volume": None,
            "Subjects": None,
            "SubSubjects": None,
            "SubSubSubjects": None,
        },
        "lan": "2",
    }
    return data

def process_documents(session, documents,logger,config_data):
    document_list = []
    sequential = 1

    for doc in documents:
        try:
            case_num = doc.get("CaseNum", f"case_{sequential}")
            ms_date = doc.get("VerdictDt")
            decision_date = parse_ms_date(ms_date)
            case_name = doc.get("CaseName", "")

            path = doc.get("PathForWeb")  # "EnglishVerdicts/99/110/001/n12"
            file_name = doc.get("FileName")  # "99001110_n12.txt"
            type_code = doc.get("TypeCode") # 3 for docx, 4 for pdf

            if not path or not file_name:
                logger.warning(f"Missing path/file for case {case_num}, skipping")
                continue

            # Determine file extension and only allow pdf/docx
            ext = determine_ext(type_code)
            if ext not in ("pdf", "docx"):
                logger.info(f"Skipping unsupported file type '{type_code}'-'{ext}' for case {case_num}")
                continue

            # Resolve config values (support dict or object)
            base_url = (
                config_data.get("base_url")
                if hasattr(config_data, "get")
                else getattr(config_data, "base_url", "")
            )
            documents_dir = (
                config_data.get("output_dir")
                if hasattr(config_data, "get")
                else getattr(config_data, "output_dir", "")
            )

            # Build real download URL
            download_url = build_download_url(base_url, path, file_name, type_code=4)

            filename_safe = sanitize_filename(
                f"{case_num}_{decision_date}_{sequential:04d}"
            )
            filepath = os.path.join(documents_dir, f"{filename_safe}.{ext}")

            logger.info(f"Downloading {filename_safe} from {download_url}")
            success, filesize = download_file(session, download_url, filepath, logger)
            status = "success" if success else "failed"

            document_list.append(
                {
                    "case_number": case_num,
                    "decision_date": decision_date,
                    "parties": case_name,
                    "document_type": ext,
                    "file_size_bytes": filesize,
                    "filename": filename_safe,
                    "download_url": download_url,
                    "download_status": status,
                }
            )

            sequential += 1
            time.sleep(1)  # optional rate limit

        except Exception as e:
            logger.error(f"Error processing document: {e}")
            continue

    return document_list
