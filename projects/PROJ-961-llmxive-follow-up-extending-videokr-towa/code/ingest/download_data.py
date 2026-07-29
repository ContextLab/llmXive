"""
Data download module for fetching VideoKR-SFT and Knowledge Graph.
"""
import hashlib
import json
import logging
import os
import sys
import requests
from pathlib import Path
from typing import Dict, Any, Optional, Union


def download_file(
    url: str,
    output_path: Union[str, Path],
    chunk_size: int = 8192
) -> Optional[Path]:
    """
    Download a file from a URL.
    
    Args:
        url (str): URL to download from.
        output_path (Union[str, Path]): Path to save the file.
        chunk_size (int): Chunk size for streaming.
        
    Returns:
        Optional[Path]: Path to the downloaded file, or None on failure.
    """
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        output_obj = Path(output_path) if isinstance(output_path, str) else output_path
        output_obj.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_obj, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
        
        return output_obj
    except Exception as e:
        logging.error(f"Failed to download {url}: {e}")
        return None


def download_videokr_sft(
    url: str,
    output_dir: Union[str, Path]
) -> Optional[Path]:
    """
    Download the VideoKR-SFT dataset.
    
    Args:
        url (str): URL to the dataset.
        output_dir (Union[str, Path]): Directory to save the dataset.
        
    Returns:
        Optional[Path]: Path to the downloaded file, or None on failure.
    """
    output_path = Path(output_dir) / "videokr_sft.json"
    return download_file(url, output_path)


def download_knowledge_graph(
    url: str,
    output_dir: Union[str, Path]
) -> Optional[Path]:
    """
    Download the Knowledge Graph.
    
    Args:
        url (str): URL to the graph.
        output_dir (Union[str, Path]): Directory to save the graph.
        
    Returns:
        Optional[Path]: Path to the downloaded file, or None on failure.
    """
    output_path = Path(output_dir) / "knowledge_graph.json"
    return download_file(url, output_path)


def verify_checksums(
    file_path: Union[str, Path],
    expected_hash: str
) -> bool:
    """
    Verify a file's checksum.
    
    Args:
        file_path (Union[str, Path]): Path to the file.
        expected_hash (str): Expected SHA-256 hash.
        
    Returns:
        bool: True if hash matches, False otherwise.
    """
    sha256_hash = hashlib.sha256()
    path_obj = Path(file_path) if isinstance(file_path, str) else file_path
    
    with open(path_obj, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    return sha256_hash.hexdigest() == expected_hash


def main() -> None:
    """Main entry point for download module."""
    pass


if __name__ == "__main__":
    main()
