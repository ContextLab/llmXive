"""
HuggingFace Downloader.
"""
import os
import logging
from pathlib import Path
from typing import Tuple
import requests
from utils.logging_config import get_logger

logger = get_logger(__name__)

def fetch_huggingface_data(repo_id: str, filename: str, local_dir: Path):
    pass
