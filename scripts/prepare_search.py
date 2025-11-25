from datetime import datetime
import json
from typing import Any, Dict
from urllib.parse import urljoin
import requests


def prepare_search_payload(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Prepare search payload for the API request."""
    return {
        "document": {
            "PublishFrom": start_date.isoformat() + "Z",
            "PublishTo": end_date.isoformat() + "Z",
            "dateType": 2,
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
            "AllSubjects": [
                {"Subject": None, "SubSubject": None, "SubSubSubject": None}
            ],
            "Old": False,
            "JudgesOperator": 2,
            "OldMainNumFormat": False,
        },
        "lan": "2",
    }


def search_documents(
    session: requests.Session,
    config: dict,
    start_date: datetime,
    end_date: datetime,
    logger,
) -> list:
    """Perform document search and return results."""
    payload = prepare_search_payload(start_date, end_date)
    search_url = urljoin(config["base_url"], config["search_path"])

    logger.info(
        f"Searching for decisions from {start_date.date()} up to {end_date.date()}"
    )

    try:
        response = session.post(search_url, json=payload, timeout=30)
        response.raise_for_status()
        logger.info(f"Search request successful (status {response.status_code})")

        results = response.json()
        documents = results.get("data", [])
        logger.info(f"Found {len(documents)} documents in search results")

        return documents

    except requests.RequestException as e:
        logger.error(f"Search request failed: {e}")
        return []
    except json.JSONDecodeError:
        logger.error("Invalid JSON response from server")
        return []