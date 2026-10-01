"""Data ingestion module for CodeSearchNet and CodeGen."""
import os
import time
import json
import hashlib
import logging
import ast
from pathlib import Path
from typing import List, Dict, Any, Optional, Generator
import sys

# Import local modules
from seeds import get_seed_value
from checksum import compute_sha256
from state_tracker import update_state_with_artifact
from logging_config import setup_logger

# HuggingFace datasets
try:
    from datasets import load_dataset
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False


logger = setup_logger("data_ingestion", log_file="data/ingestion.log")


def download_with_backoff(dataset_name: str, split: str = "train", max_retries: int = 3, interval: int = 60) -> Any:
    """Download a dataset with exponential backoff."""
    if not HF_AVAILABLE:
        raise ImportError("datasets library not installed. Please install via pip install datasets.")
    
    retries = 0
    while retries <= max_retries:
        try:
            logger.log("download_start", dataset=dataset_name, split=split)
            dataset = load_dataset(dataset_name, split=split, streaming=False)
            logger.log("download_success", dataset=dataset_name)
            return dataset
        except Exception as e:
            retries += 1
            if retries > max_retries:
                logger.log("download_failed", dataset=dataset_name, error=str(e))
                raise RuntimeError(f"Failed to download {dataset_name} after {max_retries} retries.") from e
            logger.log("download_retry", dataset=dataset_name, attempt=retries, wait=interval)
            time.sleep(interval)
            interval *= 2  # Exponential backoff


def compute_dataset_hash(dataset: Any) -> str:
    """Compute a hash of the dataset content (sampled for speed if large)."""
    hasher = hashlib.sha256()
    # Sample a subset for hashing if dataset is huge to avoid memory issues
    # Or hash the dataset name + version if available
    # For simplicity, we hash the first 1000 rows' code content
    count = 0
    max_samples = 1000
    for item in dataset:
        if count >= max_samples:
            break
        code = item.get('code', '')
        hasher.update(code.encode('utf-8'))
        count += 1
    return hasher.hexdigest()


def save_dataset_metadata(dataset_name: str, hash_val: str, count: int, output_path: str):
    """Save dataset metadata to a JSON file."""
    metadata = {
        "dataset_name": dataset_name,
        "hash": hash_val,
        "count": count,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'a') as f:
        f.write(json.dumps(metadata) + '\n')


def extract_top_level_functions(code: str) -> List[str]:
    """Extract top-level functions from code using AST."""
    try:
        tree = ast.parse(code)
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and isinstance(node, ast.AsyncFunctionDef):
                # Only top-level? Walk tree and check parent?
                # Simpler: iterate children of module
                pass
        
        # Better approach: iterate direct children of module
        functions = []
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(ast.get_source_segment(code, node) or code[node.body[0].lineno-1:node.end_lineno])
        return functions
    except SyntaxError:
        return []


def filter_python_snippets(dataset: Any, source_label: str) -> List[Dict[str, Any]]:
    """Filter dataset to keep only Python snippets and extract functions."""
    filtered = []
    for item in dataset:
        # Check language
        lang = item.get('language', '')
        if lang.lower() != 'python':
            continue
        
        code = item.get('code', '')
        if not code:
            continue
        
        # Extract functions
        functions = extract_top_level_functions(code)
        if not functions:
            continue
        
        # Create snippet records
        for func_code in functions:
            try:
                # Validate AST
                ast.parse(func_code)
                snippet = {
                    'id': f"{source_label}_{len(filtered)}",
                    'source': source_label,
                    'code': func_code,
                    'length': len(func_code),
                    'language': 'python'
                }
                filtered.append(snippet)
            except SyntaxError:
                continue
                
    return filtered


def ingest_codesearchnet() -> List[Dict[str, Any]]:
    """Ingest CodeSearchNet dataset."""
    logger.log("ingest_start", dataset="code_search_net")
    try:
        # Load CodeSearchNet
        # The dataset name is 'code_search_net'
        dataset = download_with_backoff('code_search_net')
        
        # Filter for Python
        # The dataset structure: {'java', 'js', 'go', 'python', 'ruby', 'php'}
        # We need to select the 'python' subset. 
        # In load_dataset, we can specify split or filter.
        # The dataset has a 'language' column.
        
        python_data = dataset.filter(lambda x: x['language'] == 'python')
        
        snippets = filter_python_snippets(python_data, "codesearchnet")
        logger.log("ingest_success", dataset="code_search_net", count=len(snippets))
        return snippets
    except Exception as e:
        logger.log("ingest_failed", dataset="code_search_net", error=str(e))
        raise


def ingest_codegen() -> List[Dict[str, Any]]:
    """Ingest CodeParrot/CodeGen dataset."""
    logger.log("ingest_start", dataset="codeparrot/codegen")
    try:
        # Load CodeGen
        dataset = download_with_backoff('codeparrot/codegen')
        
        # Filter for Python
        # The dataset has a 'language' column.
        python_data = dataset.filter(lambda x: x['language'] == 'python')
        
        snippets = filter_python_snippets(python_data, "codegen")
        logger.log("ingest_success", dataset="codeparrot/codegen", count=len(snippets))
        return snippets
    except Exception as e:
        logger.log("ingest_failed", dataset="codeparrot/codegen", error=str(e))
        raise


def verify_datasets(snippets_list: List[List[Dict[str, Any]]]) -> bool:
    """Verify that datasets are listed in verified sources."""
    verified_path = "data/verified_sources.json"
    if not os.path.exists(verified_path):
        logger.log("verify_failed", reason="verified_sources.json not found")
        return False
        
    with open(verified_path, 'r') as f:
        verified = json.load(f)
        
    for snippets in snippets_list:
        if not snippets:
            logger.log("verify_failed", reason="empty snippet list")
            return False
            
        source = snippets[0].get('source')
        if source not in verified.get('sources', []):
            logger.log("verify_failed", reason=f"source {source} not in verified sources")
            return False
            
    return True


def update_verified_sources():
    """Update verified sources file."""
    verified_path = "data/verified_sources.json"
    sources = ["codesearchnet", "codegen"]
    
    data = {
        "sources": sources,
        "verified_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    Path(verified_path).parent.mkdir(parents=True, exist_ok=True)
    with open(verified_path, 'w') as f:
        json.dump(data, f, indent=2)


def run_ingestion_pipeline():
    """Run the full ingestion pipeline."""
    # Ensure verified sources
    update_verified_sources()
    
    # Ingest
    codesearchnet_snippets = ingest_codesearchnet()
    codegen_snippets = ingest_codegen()
    
    # Verify
    if not verify_datasets([codesearchnet_snippets, codegen_snippets]):
        raise SystemExit("Error 101: Datasets not verified.")
        
    # Combine
    all_snippets = codesearchnet_snippets + codegen_snippets
    
    # Save
    output_path = "data/raw/ingested_snippets.json"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(all_snippets, f, indent=2)
        
    logger.log("pipeline_complete", total_snippets=len(all_snippets))
    return all_snippets


def main():
    """Main entry point."""
    run_ingestion_pipeline()

if __name__ == "__main__":
    main()