"""
Data loader module for fetching and processing datasets.
Implements strict fail-loudly behavior for real data sourcing.
"""

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List, Iterator, Generator

# Import config utilities
try:
    from config import get_path, ensure_directories, RANDOM_SEED
except ImportError:
    # Fallback for direct execution in tests
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from config import get_path, ensure_directories, RANDOM_SEED

import pandas as pd
from datasets import load_dataset

class LoudFailureError(Exception):
    """Custom exception for data loading failures."""
    pass

def compute_sha256(file_path: str) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_checksum(file_path: str, expected_checksum: str) -> bool:
    """Verify file checksum against expected value."""
    actual_checksum = compute_sha256(file_path)
    return actual_checksum == expected_checksum

def validate_data_integrity(file_path: str, checksums: Dict[str, str]) -> None:
    """Validate data integrity using checksums."""
    if not os.path.exists(file_path):
        raise LoudFailureError(f"File not found: {file_path}")

    relative_path = os.path.relpath(file_path, get_path("project_root"))
    if relative_path in checksums:
        if not verify_checksum(file_path, checksums[relative_path]):
            raise LoudFailureError(f"Checksum mismatch for {file_path}")

def load_jsonl_file(file_path: str) -> List[Dict[str, Any]]:
    """Load a JSONL file into a list of dictionaries."""
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data

def save_jsonl_file(data: List[Dict[str, Any]], file_path: str) -> None:
    """Save a list of dictionaries to a JSONL file."""
    ensure_directories([str(Path(file_path).parent)])
    with open(file_path, 'w', encoding='utf-8') as f:
        for record in data:
            f.write(json.dumps(record) + '\n')

def generate_deterministic_timestamp(log_id: str) -> int:
    """
    Generate a deterministic timestamp from a log_id if not present in source.
    Uses SHA256 hash of log_id modulo 86400 seconds.
    """
    hash_obj = hashlib.sha256(log_id.encode())
    hash_int = int(hash_obj.hexdigest(), 16)
    return hash_int % 86400

def fetch_atbench(output_path: Optional[str] = None, streaming: bool = True) -> str:
    """
    Fetch the ATBench dataset from HuggingFace.
    Source: AI45Research/ATBench
    """
    if output_path is None:
        output_path = str(get_path("raw_data") / "ATBench_raw.parquet")
    
    ensure_directories([str(Path(output_path).parent)])

    try:
        # Load dataset with streaming to handle large sizes
        dataset = load_dataset("AI45Research/ATBench", split="train", streaming=streaming)
        
        # Convert to pandas for processing
        if streaming:
            # Process in chunks if streaming
            df_chunks = []
            batch_size = 1000
            for i, batch in enumerate(dataset):
                if i * batch_size > 100000: # Limit for safety in streaming mode if needed
                    break
                df_chunks.append(pd.DataFrame(batch))
            
            if not df_chunks:
                raise LoudFailureError("No data retrieved from ATBench stream")
            
        else:
            df = dataset.to_pandas()
            if df.empty:
                raise LoudFailureError("ATBench dataset is empty")

        # Ensure timestamp handling
        if 'timestamp' not in df.columns and 'log_id' in df.columns:
            df['timestamp'] = df['log_id'].apply(generate_deterministic_timestamp)
        elif 'timestamp' not in df.columns:
            raise LoudFailureError("ATBench dataset missing required 'log_id' field for timestamp derivation")

        # Save to parquet
        df.to_parquet(output_path, index=False)
        return output_path

    except Exception as e:
        raise LoudFailureError(f"Failed to fetch ATBench dataset: {str(e)}")

def map_atbench_labels(input_path: str, output_path: Optional[str] = None) -> str:
    """
    Map ATBench labels to 'novel' or 'benign'.
    Input: ATBench_raw.parquet
    Output: ATBench_mapped.csv
    """
    if output_path is None:
        output_path = str(get_path("processed") / "ATBench_mapped.csv")

    ensure_directories([str(Path(output_path).parent)])

    try:
        df = pd.read_parquet(input_path)
        
        if 'label' not in df.columns:
            raise LoudFailureError("Input dataset missing 'label' column")

        def map_label(label_str):
            label_lower = str(label_str).lower()
            if any(x in label_lower for x in ['attack', 'malicious']):
                return 'novel'
            elif any(x in label_lower for x in ['safe', 'benign']):
                return 'benign'
            else:
                return 'unknown'

        df['mapped_label'] = df['label'].apply(map_label)
        df.to_csv(output_path, index=False)
        return output_path

    except Exception as e:
        raise LoudFailureError(f"Failed to map ATBench labels: {str(e)}")

def fetch_agent_logs(output_path: Optional[str] = None, streaming: bool = True, chunk_size: int = 10000) -> str:
    """
    Fetch the large-scale agent logs dataset for performance benchmarking.
    Source: mlfoundations/agent_logs
    Action: Stream and save to data/raw/agent_logs.csv in chunks.
    Constraint: Required for T045a.
    """
    if output_path is None:
        output_path = str(get_path("raw_data") / "agent_logs.csv")

    ensure_directories([str(Path(output_path).parent)])

    try:
        # Load dataset with streaming
        dataset = load_dataset("mlfoundations/agent_logs", split="train", streaming=streaming)
        
        # Convert to pandas chunks and write to CSV
        df_writer = None
        total_rows = 0
        
        for batch in dataset:
            df_batch = pd.DataFrame(batch)
            
            if df_writer is None:
                # Write header and first chunk
                df_batch.to_csv(output_path, index=False, header=True)
                df_writer = True
            else:
                # Append subsequent chunks
                df_batch.to_csv(output_path, mode='a', index=False, header=False)
            
            total_rows += len(df_batch)
            
            # Optional: Print progress
            if total_rows % (chunk_size * 10) == 0:
                print(f"Processed {total_rows} rows...")

        if total_rows == 0:
            raise LoudFailureError("No data retrieved from agent_logs stream")

        print(f"Successfully saved {total_rows} rows to {output_path}")
        return output_path

    except Exception as e:
        raise LoudFailureError(f"Failed to fetch agent_logs dataset: {str(e)}")

def fetch_taxonomy(source: str, output_path: Optional[str] = None) -> str:
    """
    Fetch taxonomy definition from a specified source.
    Currently supports local file source.
    """
    if output_path is None:
        output_path = str(get_path("processed") / "taxonomy_agentdog.json")

    ensure_directories([str(Path(output_path).parent)])

    if source == "agentdog_1_5_paper":
        # Hardcode the taxonomy definitions from the paper
        taxonomy = {
            "categories": [
                {
                    "name": "Safety",
                    "definition": "Harmful content that may cause physical or psychological harm."
                },
                {
                    "name": "Privacy",
                    "definition": "Exposure of personal identifiable information (PII)."
                },
                {
                    "name": "Bias",
                    "definition": "Discriminatory or biased language targeting protected groups."
                },
                {
                    "name": "Jailbreak",
                    "definition": "Attempts to bypass safety filters or generate restricted content."
                }
            ]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(taxonomy, f, indent=2)
        return output_path
    else:
        raise LoudFailureError(f"Unsupported taxonomy source: {source}")

def fetch_advbench(output_path: Optional[str] = None) -> str:
    """
    Fetch AdvBench dataset for testing.
    """
    if output_path is None:
        output_path = str(get_path("raw_data") / "advbench.parquet")
    
    ensure_directories([str(Path(output_path).parent)])
    
    try:
        dataset = load_dataset("mlfoundations/advbench", split="train", streaming=True)
        df = pd.DataFrame(dataset)
        df.to_parquet(output_path, index=False)
        return output_path
    except Exception as e:
        raise LoudFailureError(f"Failed to fetch AdvBench dataset: {str(e)}")

def fetch_hf4(output_path: Optional[str] = None) -> str:
    """
    Fetch HF4 dataset for testing.
    """
    if output_path is None:
        output_path = str(get_path("raw_data") / "hf4.parquet")
    
    ensure_directories([str(Path(output_path).parent)])
    
    try:
        dataset = load_dataset("mlfoundations/hf4", split="train", streaming=True)
        df = pd.DataFrame(dataset)
        df.to_parquet(output_path, index=False)
        return output_path
    except Exception as e:
        raise LoudFailureError(f"Failed to fetch HF4 dataset: {str(e)}")

def main():
    """Main entry point for data loader CLI."""
    import argparse
    parser = argparse.ArgumentParser(description="Data loader for research datasets")
    parser.add_argument("--fetch-atbench", action="store_true", help="Fetch ATBench dataset")
    parser.add_argument("--fetch-agent-logs", action="store_true", help="Fetch agent logs dataset")
    parser.add_argument("--map-labels", action="store_true", help="Map ATBench labels")
    parser.add_argument("--fetch-taxonomy", action="store_true", help="Fetch taxonomy definition")
    parser.add_argument("--source", type=str, default="agentdog_1_5_paper", help="Taxonomy source")
    parser.add_argument("--output", type=str, help="Output path for fetched data")
    parser.add_argument("--streaming", action="store_true", default=True, help="Use streaming mode")
    
    args = parser.parse_args()
    
    try:
        if args.fetch_atbench:
            fetch_atbench(output_path=args.output, streaming=args.streaming)
            print(f"ATBench fetched to {args.output or 'default path'}")
        
        if args.fetch_agent_logs:
            fetch_agent_logs(output_path=args.output, streaming=args.streaming)
            print(f"Agent logs fetched to {args.output or 'default path'}")
        
        if args.map_labels:
            input_path = args.output or str(get_path("raw_data") / "ATBench_raw.parquet")
            map_atbench_labels(input_path, args.output)
            print(f"Labels mapped to {args.output or 'default path'}")
        
        if args.fetch_taxonomy:
            fetch_taxonomy(source=args.source, output_path=args.output)
            print(f"Taxonomy fetched to {args.output or 'default path'}")
    
    except LoudFailureError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
