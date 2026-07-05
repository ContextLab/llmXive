"""
Orchestrator for coordinating arXiv and PubMed data fetching.

This module coordinates the arXiv and PubMed fetchers to download abstracts,
save them as raw JSONL files, and generate SHA256 checksums for reproducibility.
"""

import os
import json
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

from src.data.fetch.arxiv_fetcher import fetch_arxiv_abstracts
from src.data.fetch.pubmed_fetcher import fetch_pubmed_abstracts
from src.utils.logging import get_logger, setup_logging
from src.utils.manifest import save_reproducibility_manifest, generate_reproducibility_manifest
from src.utils.config import ensure_directories, get_random_seed


def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def save_to_jsonl(data: List[Dict[str, Any]], output_path: Path) -> None:
    """Save a list of dictionaries to a JSONL file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        for record in data:
            f.write(json.dumps(record) + '\n')


def load_from_jsonl(file_path: Path) -> List[Dict[str, Any]]:
    """Load records from a JSONL file."""
    records = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records


def run_orchestrator(
    arxiv_year_start: int = 2000,
    arxiv_year_end: int = 2024,
    pubmed_year_start: int = 2000,
    pubmed_year_end: int = 2024,
    arxiv_max_results: Optional[int] = None,
    pubmed_max_results: Optional[int] = None,
    output_dir: Optional[Path] = None,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Coordinate data fetching from arXiv and PubMed.
    
    Args:
        arxiv_year_start: Start year for arXiv fetch (default: 2000)
        arxiv_year_end: End year for arXiv fetch (default: 2024)
        pubmed_year_start: Start year for PubMed fetch (default: 2000)
        pubmed_year_end: End year for PubMed fetch (default: 2024)
        arxiv_max_results: Maximum number of arXiv records to fetch (None for unlimited)
        pubmed_max_results: Maximum number of PubMed records to fetch (None for unlimited)
        output_dir: Directory to save raw JSONL files (default: data/raw/)
        seed: Random seed for reproducibility
    
    Returns:
        Dictionary containing fetch status and file paths
    """
    # Setup logging
    setup_logging()
    logger = get_logger(__name__)
    
    # Ensure output directory exists
    if output_dir is None:
        output_dir = Path("data/raw")
    ensure_directories([output_dir])
    
    logger.info(f"Starting data fetch orchestrator")
    logger.info(f"Output directory: {output_dir}")
    
    # Get random seed
    if seed is None:
        seed = get_random_seed()
    logger.info(f"Using random seed: {seed}")
    
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "seed": seed,
        "arxiv": {},
        "pubmed": {},
        "files": {},
        "checksums": {}
    }
    
    # Fetch arXiv abstracts
    logger.info(f"Fetching arXiv abstracts from {arxiv_year_start} to {arxiv_year_end}")
    try:
        arxiv_data = fetch_arxiv_abstracts(
            year_start=arxiv_year_start,
            year_end=arxiv_year_end,
            max_results=arxiv_max_results
        )
        
        arxiv_output_path = output_dir / "arxiv_abstracts.jsonl"
        save_to_jsonl(arxiv_data, arxiv_output_path)
        
        arxiv_checksum = compute_sha256(arxiv_output_path)
        
        results["arxiv"] = {
            "status": "success",
            "record_count": len(arxiv_data),
            "year_range": f"{arxiv_year_start}-{arxiv_year_end}"
        }
        results["files"]["arxiv"] = str(arxiv_output_path)
        results["checksums"]["arxiv"] = arxiv_checksum
        
        logger.info(f"Saved {len(arxiv_data)} arXiv records to {arxiv_output_path}")
        logger.info(f"arXiv checksum: {arxiv_checksum}")
        
    except Exception as e:
        logger.error(f"Failed to fetch arXiv data: {str(e)}")
        results["arxiv"] = {
            "status": "failed",
            "error": str(e)
        }
    
    # Fetch PubMed abstracts
    logger.info(f"Fetching PubMed abstracts from {pubmed_year_start} to {pubmed_year_end}")
    try:
        pubmed_data = fetch_pubmed_abstracts(
            year_start=pubmed_year_start,
            year_end=pubmed_year_end,
            max_results=pubmed_max_results
        )
        
        pubmed_output_path = output_dir / "pubmed_abstracts.jsonl"
        save_to_jsonl(pubmed_data, pubmed_output_path)
        
        pubmed_checksum = compute_sha256(pubmed_output_path)
        
        results["pubmed"] = {
            "status": "success",
            "record_count": len(pubmed_data),
            "year_range": f"{pubmed_year_start}-{pubmed_year_end}"
        }
        results["files"]["pubmed"] = str(pubmed_output_path)
        results["checksums"]["pubmed"] = pubmed_checksum
        
        logger.info(f"Saved {len(pubmed_data)} PubMed records to {pubmed_output_path}")
        logger.info(f"PubMed checksum: {pubmed_checksum}")
        
    except Exception as e:
        logger.error(f"Failed to fetch PubMed data: {str(e)}")
        results["pubmed"] = {
            "status": "failed",
            "error": str(e)
        }
    
    # Generate and save reproducibility manifest
    manifest_path = Path("results/manifest.json")
    ensure_directories([manifest_path.parent])
    
    manifest_data = generate_reproducibility_manifest(
        task_id="T013",
        parameters={
            "arxiv_year_start": arxiv_year_start,
            "arxiv_year_end": arxiv_year_end,
            "pubmed_year_start": pubmed_year_start,
            "pubmed_year_end": pubmed_year_end,
            "arxiv_max_results": arxiv_max_results,
            "pubmed_max_results": pubmed_max_results,
            "seed": seed
        },
        outputs={
            "arxiv_file": results["files"].get("arxiv"),
            "pubmed_file": results["files"].get("pubmed"),
            "arxiv_checksum": results["checksums"].get("arxiv"),
            "pubmed_checksum": results["checksums"].get("pubmed")
        },
        status={
            "arxiv_fetch_status": results["arxiv"]["status"],
            "pubmed_fetch_status": results["pubmed"]["status"]
        }
    )
    
    save_reproducibility_manifest(manifest_path, manifest_data)
    logger.info(f"Saved reproducibility manifest to {manifest_path}")
    
    return results


def main():
    """Main entry point for the orchestrator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Orchestrate data fetching from arXiv and PubMed")
    parser.add_argument("--arxiv-start", type=int, default=2000, help="Start year for arXiv")
    parser.add_argument("--arxiv-end", type=int, default=2024, help="End year for arXiv")
    parser.add_argument("--pubmed-start", type=int, default=2000, help="Start year for PubMed")
    parser.add_argument("--pubmed-end", type=int, default=2024, help="End year for PubMed")
    parser.add_argument("--arxiv-max", type=int, default=None, help="Max arXiv records")
    parser.add_argument("--pubmed-max", type=int, default=None, help="Max PubMed records")
    parser.add_argument("--output-dir", type=str, default="data/raw", help="Output directory")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    
    args = parser.parse_args()
    
    results = run_orchestrator(
        arxiv_year_start=args.arxiv_start,
        arxiv_year_end=args.arxiv_end,
        pubmed_year_start=args.pubmed_start,
        pubmed_year_end=args.pubmed_end,
        arxiv_max_results=args.arxiv_max,
        pubmed_max_results=args.pubmed_max,
        output_dir=Path(args.output_dir),
        seed=args.seed
    )
    
    print("\n=== Fetch Results ===")
    print(f"arXiv status: {results['arxiv'].get('status', 'unknown')}")
    if results['arxiv'].get('status') == 'success':
        print(f"  Records: {results['arxiv'].get('record_count', 0)}")
        print(f"  File: {results['files'].get('arxiv')}")
        print(f"  Checksum: {results['checksums'].get('arxiv')}")
    
    print(f"PubMed status: {results['pubmed'].get('status', 'unknown')}")
    if results['pubmed'].get('status') == 'success':
        print(f"  Records: {results['pubmed'].get('record_count', 0)}")
        print(f"  File: {results['files'].get('pubmed')}")
        print(f"  Checksum: {results['checksums'].get('pubmed')}")
    
    print(f"\nManifest saved to: results/manifest.json")

if __name__ == "__main__":
    main()