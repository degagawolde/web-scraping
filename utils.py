import json
import logging
import os
from datetime import datetime
from typing import Dict, Any

import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry


def setup_session(config: Dict[str, Any], logger) -> requests.Session:
    """Configure HTTP session with retries, headers, and cookies."""
    session = requests.Session()
    session.headers.update(config.get("headers", {}))
    session.cookies.update(config.get("cookies", {}))

    retry_strategy = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "POST", "GET", "OPTIONS"],
        raise_on_status=False,
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    logger.debug("HTTP session initialized with retries, headers, and cookies")
    return session


# Configure logging
def setup_logging(output_dir: str) -> logging.Logger:
    """Configure logging with file and console handlers."""
    os.makedirs(output_dir, exist_ok=True)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")

    # File handler
    file_handler = logging.FileHandler(os.path.join(output_dir, "scraper.log"))
    file_handler.setFormatter(formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def load_config(config_path: str = "config.json") -> dict:
    """Load configuration from JSON file."""
    with open(config_path, "r") as config_file:
        return json.load(config_file)