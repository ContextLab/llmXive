"""
Script to download the HumanEval dataset.
"""
import os
import json
import requests
from pathlib import Path

from code.config import DATA_RAW_DIR

HUMAN_EVAL_URL = "https://raw.githubusercontent.com/openai/human-eval/master/data/human-eval-v1-20210807.jsonl"
OUTPUT_PATH = os.path.join(DATA_RAW_DIR, "human_eval_data.jsonl")

def download_human_eval():
    """Downloads the HumanEval dataset from the official GitHub repo."""
    print(f"Downloading HumanEval dataset from: {HUMAN_EVAL_URL}")
    print(f"Saving to: {OUTPUT_PATH}")

    # Ensure the data/raw directory exists before saving
    Path(DATA_RAW_DIR).mkdir(parents=True, exist_ok=True)

    try:
        response = requests.get(HUMAN_EVAL_URL, stream=True)
        response.raise_for_status()

        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            line_count = 0
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk.decode("utf-8"))
                    line_count += chunk.decode("utf-8").count('\n')

        print(f"Successfully downloaded and saved {line_count} problems to {OUTPUT_PATH}")
        return True
    except Exception as e:
        print(f"Failed to download dataset: {e}")
        raise e

if __name__ == "__main__":
    download_human_eval()
