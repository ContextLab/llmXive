"""
Reproducibility Reporting Utility.

Implements T006: Generate reproducibility_report.json.
"""
import json
import os
import hashlib
import platform
import subprocess
import time
from typing import Dict, Any, List, Optional
from pathlib import Path

def get_git_commit() -> str:
    try:
        result = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except Exception:
        return "unknown"

def get_file_checksum(file_path: str) -> str:
    if not os.path.exists(file_path):
        return "missing"
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_directory_checksums(dir_path: str) -> Dict[str, str]:
    checksums = {}
    for root, _, files in os.walk(dir_path):
        for file in files:
            full_path = os.path.join(root, file)
            checksums[full_path] = get_file_checksum(full_path)
    return checksums

def get_resource_usage() -> Dict[str, Any]:
    # Re-implement or import from utils.logging if available
    # For standalone safety, simple implementation here
    import psutil
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return {
        "rss_mb": mem_info.rss / (1024 * 1024),
        "vms_mb": mem_info.vms / (1024 * 1024),
        "cpu_percent": process.cpu_percent()
    }

def calculate_artifact_checksums(artifact_dirs: List[str]) -> Dict[str, Dict[str, str]]:
    results = {}
    for d in artifact_dirs:
        if os.path.exists(d):
            results[d] = get_directory_checksums(d)
    return results

def load_validation_metrics(file_path: str) -> Dict[str, Any]:
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    return {}

def generate_report(
    git_commit: str,
    artifacts: Dict[str, Dict[str, str]],
    validation_metrics: Dict[str, Any],
    resource_usage: Dict[str, Any]
) -> Dict[str, Any]:
    return {
        "git_commit": git_commit,
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "artifacts_checksums": artifacts,
        "validation_metrics": validation_metrics,
        "resource_usage": resource_usage,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }

def save_report(report: Dict[str, Any], output_path: str):
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Reproducibility report saved to {output_path}")
