import os
import sys
import json
import hashlib
from pathlib import Path

def compute_sha256(path):
    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def hash_artifacts():
    return {}

def main():
    pass
