from datetime import datetime
import json
from typing import Any, Dict, List
from urllib.parse import urljoin
import requests


def prepare_search_payload(
    start_date: datetime,
    end_date: datetime,
    decision_type: List[int],
    case_type: List[int],
    keywords: str,
) -> Dict[str, Any]:
    """Prepare search payload for the API request."""
    return {
        "document": {
            "PublishFrom": start_date.isoformat() + "Z",
            "PublishTo": end_date.isoformat() + "Z",
            "dateType": 2,
            "publishDate": 8,
            "translationDateType": 1,
            "translationPublishFrom": start_date.isoformat() + "Z",
            "translationPublishTo": end_date.isoformat() + "Z",
            "translationPublishDate": 8,
            "CodeTypes": [d_type for d_type in decision_type],
            "CodeMador": [c_type for c_type in case_type],
            "SearchText": [
                {
                    "Text": keywords,
                    "textOperator": 1,
                    "option": "2",
                    "Inverted": False,
                    "Synonym": False,
                    "NearDistance": 3,
                    "MatchOrder": False,
                }
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
    decision_type: List[int],
    case_type: List[int],
    keywords: List[str],
    logger,
) -> list:
    """Perform document search and return results."""
    payload = prepare_search_payload(start_date, end_date,decision_type,case_type,keywords)
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
