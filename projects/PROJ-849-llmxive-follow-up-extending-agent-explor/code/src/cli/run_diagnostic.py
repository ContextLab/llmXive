"""
Main entry point for the Semantic Divergence Diagnostic pipeline.
Orchestrates loading, retrieval, scoring, and reporting.
"""

import os
import sys
import json
import logging
import time
import signal
from pathlib import Path
from typing import List, Dict, Any

# Project root setup
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from src.lib.config import ensure_directories, RANDOM_SEED
from src.lib.errors import TimeoutExceededError, MemoryLimitExceededError
from src.lib.resource_tracker import ResourceTracker
from src.lib.data_loader import load_data, save_filtered_dataset
from src.lib.tool_mapper import get_all_tool_descriptions
from src.services.retrieval_service import create_retrieval_service, retrieve_top_tools
from src.models.divergence_model import DivergenceModel, process_problem
from src.services.analysis_service import save_analysis_report

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(PROJECT_ROOT / "results" / "diagnostic.log")
    ]
)
logger = logging.getLogger(__name__)

def load_and_validate_data(data_path: str) -> List[Dict[str, Any]]:
    """Load raw data and perform initial validation."""
    logger.info(f"Loading data from: {data_path}")
    data = load_data(data_path)
    
    if not data:
        raise ValueError("Data loader returned empty dataset.")
    
    logger.info(f"Loaded {len(data)} records.")
    return data

def run_retrieval_and_scoring(
    data: List[Dict[str, Any]], 
    tool_descriptions: List[str],
    output_path: str
) -> List[Dict[str, Any]]:
    """Run retrieval and divergence scoring for all problems."""
    logger.info("Initializing Retrieval Service...")
    retrieval_service = create_retrieval_service(tool_descriptions)
    
    divergence_model = DivergenceModel()
    results = []

    for idx, record in enumerate(data):
        try:
            problem_id = record.get("problem_id", f"unknown_{idx}")
            thinking_prefix = record.get("thinking", "")
            
            if not thinking_prefix:
                logger.warning(f"Record {problem_id} missing 'thinking' prefix. Skipping.")
                continue

            # Retrieve tools
            retrieved_tools = retrieve_top_tools(retrieval_service, thinking_prefix, top_k=10)
            
            # Calculate divergence
            divergence_result = process_problem(
                thinking_prefix=thinking_prefix,
                tool_descriptions=retrieved_tools,
                model=divergence_model
            )
            
            results.append({
                "problem_id": problem_id,
                "thinking_embedding": divergence_result.thinking_embedding.tolist() if hasattr(divergence_result.thinking_embedding, 'tolist') else [],
                "tool_centroid_embedding": divergence_result.tool_centroid_embedding.tolist() if hasattr(divergence_result.tool_centroid_embedding, 'tolist') else [],
                "cosine_similarity": divergence_result.cosine_similarity,
                "semantic_divergence_score": divergence_result.semantic_divergence_score
            })

            if (idx + 1) % 50 == 0:
                logger.info(f"Processed {idx + 1} records...")

        except Exception as e:
            logger.error(f"Error processing problem {problem_id}: {e}")
            continue

    logger.info(f"Saving results to: {output_path}")
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    
    return results

def save_results(results: List[Dict[str, Any]], output_path: str):
    """Save final results to JSON."""
    logger.info(f"Writing final results to {output_path}")
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

def run_diagnostic():
    """
    Main orchestration function.
    Wraps execution with resource limits and error handling.
    """
    ensure_directories()
    
    data_path = str(PROJECT_ROOT / "data" / "raw" / "problems.json")
    output_path = str(PROJECT_ROOT / "results" / "divergence_scores.json")
    error_log_path = str(PROJECT_ROOT / "results" / "error_log.txt")

    logger.info("Starting Semantic Divergence Diagnostic...")

    # Initialize Resource Tracker
    tracker = ResourceTracker()

    try:
        # 1. Load Data
        data = load_and_validate_data(data_path)
        
        # 2. Get Tool Descriptions
        logger.info("Loading tool mappings...")
        # Assuming tool_mapper loads from a fixed path or data is embedded
        # Using the API from T006
        from src.lib.tool_mapper import load_tool_mapping
        # Load the specific mapping file
        tool_mapping = load_tool_mapping(str(PROJECT_ROOT / "data" / "tool_mappings" / "mathvista_tool_map.json"))
        all_tools = get_all_tool_descriptions(tool_mapping)
        
        # 3. Run Retrieval and Scoring
        results = run_retrieval_and_scoring(data, all_tools, output_path)
        
        # 4. Save Results
        save_results(results, output_path)
        
        logger.info("Diagnostic completed successfully.")

    except TimeoutExceededError:
        logger.error("Timeout Exceeded")
        with open(error_log_path, "w") as f:
            f.write("Timeout Exceeded")
        sys.exit(1)
    
    except MemoryLimitExceededError:
        logger.error("Memory Limit Exceeded")
        with open(error_log_path, "w") as f:
            f.write("Memory Limit Exceeded")
        sys.exit(1)
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        # Re-raise or handle generic errors
        raise

if __name__ == "__main__":
    run_diagnostic()
