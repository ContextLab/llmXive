import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any
import time

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lib.config import DATA_DIR, RESULTS_DIR, LOG_LEVEL
from lib.data_loader import load_real_data, load_tool_mapping
from lib.tool_mapper import ToolMapper
from services.retrieval_service import RetrievalService
from models.divergence_model import process_problem, get_model_and_tokenizer
from services.analysis_service import run_analysis

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(str(RESULTS_DIR / "diagnostic_run.log"))
    ]
)
logger = logging.getLogger(__name__)

def load_and_validate_data() -> List[Dict[str, Any]]:
    """
    Load real data and validate it.
    Returns a list of problem records.
    """
    logger.info("Loading real data...")
    try:
        data = load_real_data()
        if not data:
            logger.error("No data loaded. Exiting.")
            return []
        
        logger.info(f"Loaded {len(data)} records.")
        return data
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        raise

def run_retrieval_and_scoring(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Run retrieval and scoring for all problems in the dataset.
    """
    logger.info("Starting retrieval and scoring process...")
    
    # Initialize tool mapper
    tool_mapper = ToolMapper()
    tool_descriptions = tool_mapper.get_all_tool_descriptions()
    
    if not tool_descriptions:
        logger.error("No tool descriptions found. Cannot proceed with retrieval.")
        return []
    
    logger.info(f"Loaded {len(tool_descriptions)} tool descriptions.")
    
    # Initialize model and tokenizer once
    model, tokenizer = get_model_and_tokenizer()
    
    results = []
    total = len(data)
    
    for i, record in enumerate(data):
        if i % 50 == 0:
            logger.info(f"Processing record {i}/{total}")
        
        thinking_prefix = record.get("thinking", "")
        if not thinking_prefix:
            logger.warning(f"Record {i} missing 'thinking' field. Skipping.")
            continue
        
        # Get tool descriptions for this problem
        problem_tools = tool_mapper.get_tool_descriptions_for_problem(record)
        if not problem_tools:
            logger.warning(f"Record {i} has no tool descriptions. Skipping.")
            continue
        
        # Process the problem
        try:
            result = process_problem(
                thinking_prefix=thinking_prefix,
                tool_descriptions=problem_tools,
                model=model,
                tokenizer=tokenizer
            )
            result["problem_id"] = record.get("problem_id", f"unknown_{i}")
            results.append(result)
        except Exception as e:
            logger.error(f"Error processing record {i}: {e}")
            continue
    
    logger.info(f"Completed scoring for {len(results)} problems.")
    return results

def save_results(results: List[Dict[str, Any]]):
    """
    Save results to a JSON file.
    """
    output_path = RESULTS_DIR / "divergence_scores.json"
    logger.info(f"Saving results to {output_path}")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Saved {len(results)} results.")

def run_diagnostic():
    """
    Main entry point for running the diagnostic.
    """
    start_time = time.time()
    logger.info("Starting Semantic Divergence Diagnostic...")
    
    try:
        # Load data
        data = load_and_validate_data()
        if not data:
            logger.error("Data loading failed. Aborting.")
            return
        
        # Run retrieval and scoring
        results = run_retrieval_and_scoring(data)
        if not results:
            logger.error("No results generated. Aborting.")
            return
        
        # Save results
        save_results(results)
        
        # Run analysis (correlation, etc.)
        logger.info("Running analysis...")
        analysis_report = run_analysis()
        
        # Save analysis report
        analysis_path = RESULTS_DIR / "analysis_report.json"
        with open(analysis_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_report, f, indent=2)
        logger.info(f"Analysis report saved to {analysis_path}")
        
        elapsed = time.time() - start_time
        logger.info(f"Diagnostic completed successfully in {elapsed:.2f} seconds.")
        
    except Exception as e:
        logger.error(f"Diagnostic failed: {e}")
        raise

if __name__ == "__main__":
    run_diagnostic()