import os
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any, Generator
from datasets import load_dataset
import hashlib

# Import from project API surface
from seeds import get_seed_value
from logging_config import get_logger
from checksum import register_dataset_checksum
from verified_sources_updater import load_verified_sources

# Constants
MAX_TOTAL_SNIPPETS = 10000
DATA_DIR = Path("data")
PROCESSED_DIR = DATA_DIR / "processed"
LOG_FILE = Path("results") / "pipeline.log"

# Ensure directories exist
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
Path("results").mkdir(parents=True, exist_ok=True)

logger = get_logger(__name__)

def get_sample_fraction(total_available: int, target_max: int = MAX_TOTAL_SNIPPETS) -> float:
    """
    Calculate the sample fraction to ensure total snippets <= target_max.
    Returns a float between 0.0 and 1.0.
    """
    if total_available <= 0:
        return 0.0
    fraction = min(1.0, target_max / total_available)
    return fraction

def stream_and_sample_dataset(
    dataset_name: str,
    split: str = "train",
    target_count: int = 5000,  # Target per dataset (5k + 5k = 10k total)
    streaming: bool = True
) -> Generator[Dict[str, Any], None, None]:
    """
    Load dataset in streaming mode and yield up to target_count items.
    Uses a simple counter to stop after target_count items.
    """
    logger.info(f"Starting streaming load for {dataset_name}, split={split}, target={target_count}")
    
    try:
        # Load dataset in streaming mode
        ds = load_dataset(dataset_name, split=split, streaming=streaming)
        
        count = 0
        for item in ds:
            if count >= target_count:
                break
            yield item
            count += 1
        
        logger.info(f"Streamed {count} items from {dataset_name}")
        return count
    except Exception as e:
        logger.error(f"Error streaming dataset {dataset_name}: {e}")
        raise

def process_codesearchnet_stream(
    target_count: int = 5000,
    output_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process CodeSearchNet dataset with streaming and sampling.
    Returns metadata about the processed dataset.
    """
    logger.info("Processing CodeSearchNet with streaming and sampling")
    
    processed_snippets = []
    count = 0
    
    try:
        # Use streaming to avoid loading full dataset into memory
        ds = load_dataset("code_search_net", "python", split="train", streaming=True)
        
        for item in ds:
            if count >= target_count:
                break
            
            # Extract relevant fields (CodeSearchNet structure)
            snippet = {
                "id": f"csnet_{count}",
                "source": "code_search_net",
                "code": item.get("code", ""),
                "language": "python",
                "length": len(item.get("code", "")),
                "repo": item.get("repo", "unknown"),
                "path": item.get("path", "unknown")
            }
            
            if snippet["code"]:  # Only keep non-empty code
                processed_snippets.append(snippet)
                count += 1
    
        logger.info(f"Processed {count} valid snippets from CodeSearchNet")
        
        # Write to output file if specified
        if output_file:
            output_path = Path(output_file)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(processed_snippets, f, indent=2)
            logger.info(f"Saved {count} snippets to {output_file}")
        
        return {
            "source": "code_search_net",
            "count": count,
            "output_file": output_file,
            "status": "completed"
        }
        
    except Exception as e:
        logger.error(f"Error processing CodeSearchNet stream: {e}")
        raise

def process_codegen_stream(
    target_count: int = 5000,
    output_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process CodeParrot/CodeGen dataset with streaming and sampling.
    Returns metadata about the processed dataset.
    """
    logger.info("Processing CodeParrot/CodeGen with streaming and sampling")
    
    processed_snippets = []
    count = 0
    
    try:
        # Use streaming to avoid loading full dataset into memory
        ds = load_dataset("codeparrot/codegen", split="train", streaming=True)
        
        for item in ds:
            if count >= target_count:
                break
            
            # Extract relevant fields (CodeGen structure may vary)
            code_text = item.get("code", "") or item.get("text", "")
            
            snippet = {
                "id": f"codegen_{count}",
                "source": "codeparrot_codegen",
                "code": code_text,
                "language": "python",
                "length": len(code_text),
                "repo": "generated",
                "path": "generated"
            }
            
            if code_text:  # Only keep non-empty code
                processed_snippets.append(snippet)
                count += 1
    
        logger.info(f"Processed {count} valid snippets from CodeParrot/CodeGen")
        
        # Write to output file if specified
        if output_file:
            output_path = Path(output_file)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(processed_snippets, f, indent=2)
            logger.info(f"Saved {count} snippets to {output_file}")
        
        return {
            "source": "codeparrot_codegen",
            "count": count,
            "output_file": output_file,
            "status": "completed"
        }
        
    except Exception as e:
        logger.error(f"Error processing CodeParrot/CodeGen stream: {e}")
        raise

def run_sampling_workflow() -> Dict[str, Any]:
    """
    Main workflow to stream and sample both datasets to ensure total <= 10,000.
    Distributes the limit roughly equally between human-written and LLM-generated.
    """
    logger.info("Starting sampling workflow with 10,000 snippet limit")
    
    results = {
        "human_written": {},
        "llm_generated": {},
        "total_count": 0,
        "limit": MAX_TOTAL_SNIPPETS,
        "status": "completed"
    }
    
    # Verify datasets first
    try:
        verified = load_verified_sources()
        if "code_search_net" not in verified.get("sources", {}):
            logger.warning("CodeSearchNet not in verified sources, attempting to verify")
        if "codeparrot_codegen" not in verified.get("sources", {}):
            logger.warning("CodeParrot/CodeGen not in verified sources, attempting to verify")
    except Exception as e:
        logger.warning(f"Could not load verified sources: {e}")
    
    # Process CodeSearchNet (human-written)
    csnet_output = DATA_DIR / "processed" / "codesearchnet_sampled.json"
    try:
        csnet_result = process_codesearchnet_stream(
            target_count=5000,
            output_file=str(csnet_output)
        )
        results["human_written"] = csnet_result
        results["total_count"] += csnet_result["count"]
    except Exception as e:
        results["human_written"] = {"status": "failed", "error": str(e)}
        logger.error(f"Failed to process CodeSearchNet: {e}")
    
    # Process CodeParrot/CodeGen (LLM-generated)
    codegen_output = DATA_DIR / "processed" / "codegen_sampled.json"
    try:
        codegen_result = process_codegen_stream(
            target_count=5000,
            output_file=str(codegen_output)
        )
        results["llm_generated"] = codegen_result
        results["total_count"] += codegen_result["count"]
    except Exception as e:
        results["llm_generated"] = {"status": "failed", "error": str(e)}
        logger.error(f"Failed to process CodeParrot/CodeGen: {e}")
    
    # Validate total count
    if results["total_count"] > MAX_TOTAL_SNIPPETS:
        logger.warning(f"Total snippets ({results['total_count']}) exceeds limit ({MAX_TOTAL_SNIPPETS})")
        results["status"] = "warning"
    else:
        logger.info(f"Total snippets ({results['total_count']}) within limit ({MAX_TOTAL_SNIPPETS})")
    
    # Save workflow results
    results_file = DATA_DIR / "processed" / "sampling_results.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Sampling workflow completed. Results saved to {results_file}")
    return results

def main():
    """
    Entry point for the data sampling module.
    """
    logger.info("Running data sampling module")
    results = run_sampling_workflow()
    
    # Print summary
    print("\n=== Sampling Workflow Summary ===")
    print(f"Human-written (CodeSearchNet): {results['human_written'].get('count', 0)} snippets")
    print(f"LLM-generated (CodeGen): {results['llm_generated'].get('count', 0)} snippets")
    print(f"Total: {results['total_count']} / {MAX_TOTAL_SNIPPETS} limit")
    print(f"Status: {results['status']}")
    
    if results["total_count"] > MAX_TOTAL_SNIPPETS:
        print("WARNING: Exceeded snippet limit!")
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
