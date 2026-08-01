import logging
import os
import sys
import json
import csv
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
import datetime

def setup_logging(log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger("llmXive")
    logger.setLevel(level)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)

def ensure_directories(paths: List[Path]):
    for p in paths:
        p.mkdir(parents=True, exist_ok=True)

def write_json(path: Path, data: Dict[str, Any]):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def read_json(path: Path) -> Dict[str, Any]:
    with open(path, 'r') as f:
        return json.load(f)

def write_csv(path: Path, data: List[Dict[str, Any]]):
    if not data:
        return
    with open(path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

def read_csv(path: Path) -> List[Dict[str, Any]]:
    with open(path, 'r') as f:
        reader = csv.DictReader(f)
        return list(reader)

def safe_delete(path: Path):
    if path.exists():
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()

def handle_error(error: Exception, message: str = "An error occurred"):
    logging.error(f"{message}: {str(error)}")
    raise error

def validate_file_exists(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

def get_timestamp_filename(prefix: str = "output", ext: str = ".csv") -> str:
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}{ext}"

def format_size(size_bytes: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"
