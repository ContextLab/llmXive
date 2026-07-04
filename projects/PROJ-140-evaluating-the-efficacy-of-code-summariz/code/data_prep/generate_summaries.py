"""
Generate code summaries for bug localization study.

Implements:
1. Deterministic "LLM-Sim" generator (CPU-tractable)
2. Rule-based srcML comment extractor fallback
3. Handles generation failure/timeout gracefully
4. Outputs: data/summaries/llm_sim_summaries.csv and data/summaries/rule_summaries.csv
"""

import os
import sys
import csv
import json
import time
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import xml.etree.ElementTree as ET

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.config_manager import get_config
from utils.logging_utils import setup_logging, get_logger
from utils.hash_artifacts import hash_file

# Configure logging
logger = get_logger(__name__)

# Constants
LLM_SIM_OUTPUT_PATH = PROJECT_ROOT / "data" / "summaries" / "llm_sim_summaries.csv"
RULE_SUMMARY_OUTPUT_PATH = PROJECT_ROOT / "data" / "summaries" / "rule_summaries.csv"
DEFECTS4J_DATA_PATH = PROJECT_ROOT / "data" / "defects4j" / "stratified_methods.json"

def load_stratified_methods() -> List[Dict[str, Any]]:
    """Load stratified buggy methods from T013 output."""
    if not DEFECTS4J_DATA_PATH.exists():
        raise FileNotFoundError(f"Stratified methods file not found: {DEFECTS4J_DATA_PATH}. "
                              "Please run T013 (download_defects4j.py) first.")
    
    with open(DEFECTS4J_DATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_first_comment_line(code_text: str) -> Optional[str]:
    """
    Extract the first comment line from code text.
    Handles both // and /* */ style comments.
    """
    if not code_text:
        return None
    
    # Try single-line comments first
    single_line_match = re.search(r'//\s*(.+?)(?:\n|$)', code_text)
    if single_line_match:
        comment = single_line_match.group(1).strip()
        # Clean up trailing asterisks or closing brackets
        comment = re.sub(r'\s*\*/\s*$', '', comment)
        return comment if comment else None
    
    # Try multi-line comments
    multi_line_match = re.search(r'/\*\s*(.+?)(?:\*/|$)', code_text, re.DOTALL)
    if multi_line_match:
        comment = multi_line_match.group(1).strip()
        # Take first line only
        first_line = comment.split('\n')[0].strip()
        # Remove leading asterisks
        first_line = re.sub(r'^\s*\*\s*', '', first_line)
        return first_line if first_line else None
    
    return None

def parse_method_signature(code_text: str) -> Tuple[str, str, str]:
    """
    Parse method name, parameters, and return type from code text.
    Returns (method_name, params_str, return_type)
    """
    if not code_text:
        return "unknown", "No parameters", "unknown"
    
    # Common patterns for Java method signatures
    # Pattern 1: public/protected/private return_type method_name(params)
    pattern = r'(?:public|protected|private|static|final|abstract|synchronized|native|strictfp)\s+' \
             r'(?:[\w<>[\],\s]+\s+)?' \
             r'(\w+)\s*\(([^)]*)\)'
    
    match = re.search(pattern, code_text)
    if match:
        method_name = match.group(1)
        params_str = match.group(2).strip()
        
        # Extract return type (simplified)
        return_pattern = r'^(?:public|protected|private|static|final|abstract|synchronized|native|strictfp)\s+(\w+)'
        return_match = re.search(return_pattern, code_text)
        return_type = return_match.group(1) if return_match else "unknown"
        
        # Format parameters
        if not params_str or params_str == "":
            params_formatted = "No parameters"
        else:
            # Count parameters
            param_list = [p.strip() for p in params_str.split(',') if p.strip()]
            if len(param_list) == 1:
                params_formatted = f"1 parameter: {param_list[0]}"
            else:
                params_formatted = f"{len(param_list)} parameters: {params_str}"
        
        return method_name, params_formatted, return_type
    
    # Fallback: try to find any method-like pattern
    fallback_pattern = r'(\w+)\s*\(([^)]*)\)'
    fallback_match = re.search(fallback_pattern, code_text)
    if fallback_match:
        return fallback_match.group(1), "Unknown signature", "unknown"
    
    return "unknown", "No parameters", "unknown"

def generate_llm_sim_summary(method_data: Dict[str, Any], timeout_seconds: float = 2.0) -> Optional[Dict[str, Any]]:
    """
    Deterministic "LLM-Sim" generator mimicking LLM structure.
    Uses template: "Method: <name>\nParams: <args>\nReturns: <type>\nComment: <first_comment_line>"
    
    Args:
        method_data: Dictionary containing method information
        timeout_seconds: Simulated timeout for generation (default 2.0s)
    
    Returns:
        Dictionary with summary or None if generation fails
    """
    start_time = time.time()
    
    try:
        # Extract method information
        code_text = method_data.get('code', '')
        method_id = method_data.get('method_id', 'unknown')
        project_id = method_data.get('project_id', 'unknown')
        
        # Parse method signature
        method_name, params_str, return_type = parse_method_signature(code_text)
        
        # Extract comment
        comment = extract_first_comment_line(code_text)
        if not comment:
            comment = "No comment available"
        
        # Build deterministic summary using template
        summary_text = f"Method: {method_name}\nParams: {params_str}\nReturns: {return_type}\nComment: {comment}"
        
        # Simulate LLM processing time (deterministic based on method_id for reproducibility)
        # Use a simple hash to generate consistent "processing time"
        hash_val = hash(method_id) % 1000
        simulated_delay = 0.1 + (hash_val / 10000)  # 0.1s to 0.2s range
        
        # Check if simulated delay exceeds timeout
        if simulated_delay > timeout_seconds:
            logger.warning(f"Simulated timeout for method {method_id}, falling back to rule-based")
            return None
        
        # Add small real delay to simulate actual processing
        time.sleep(simulated_delay)
        
        # Check elapsed time
        elapsed = time.time() - start_time
        if elapsed > timeout_seconds:
            logger.warning(f"Timeout exceeded for method {method_id} ({elapsed:.2f}s)")
            return None
        
        return {
            'method_id': method_id,
            'project_id': project_id,
            'summary_text': summary_text,
            'generation_method': 'llm_sim',
            'processing_time_ms': int(elapsed * 1000),
            'success': True
        }
        
    except Exception as e:
        logger.error(f"LLM-Sim generation failed for method {method_id}: {str(e)}")
        return None

def generate_rule_summary(method_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Rule-based summary generator using srcML-style extraction.
    
    Args:
        method_data: Dictionary containing method information
    
    Returns:
        Dictionary with summary or None if extraction fails
    """
    try:
        code_text = method_data.get('code', '')
        method_id = method_data.get('method_id', 'unknown')
        project_id = method_data.get('project_id', 'unknown')
        
        if not code_text:
            logger.warning(f"No code found for method {method_id}")
            return None
        
        # Parse method signature
        method_name, params_str, return_type = parse_method_signature(code_text)
        
        # Extract comment
        comment = extract_first_comment_line(code_text)
        if not comment:
            comment = "No comment available"
        
        # Build rule-based summary
        summary_text = f"[RULE] Method: {method_name}\nParams: {params_str}\nReturns: {return_type}\nComment: {comment}"
        
        return {
            'method_id': method_id,
            'project_id': project_id,
            'summary_text': summary_text,
            'generation_method': 'rule_based',
            'processing_time_ms': 0,
            'success': True
        }
        
    except Exception as e:
        logger.error(f"Rule-based generation failed for method {method_id}: {str(e)}")
        return None

def save_summaries_to_csv(summaries: List[Dict[str, Any]], output_path: Path):
    """Save summaries to CSV file."""
    if not summaries:
        logger.warning(f"No summaries to save for {output_path}")
        return
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = ['method_id', 'project_id', 'summary_text', 'generation_method', 
                 'processing_time_ms', 'success']
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for summary in summaries:
            writer.writerow(summary)
    
    logger.info(f"Saved {len(summaries)} summaries to {output_path}")
    
    # Generate hash for versioning
    if output_path.exists():
      hash_value = hash_file(output_path)
      logger.info(f"Generated hash for {output_path}: {hash_value}")

def main():
    """Main entry point for summary generation."""
    logger.info("Starting summary generation process...")
    
    # Load configuration
    config = get_config()
    timeout_seconds = config.get('summary_generation', {}).get('timeout_seconds', 2.0)
    
    # Load stratified methods
    try:
        methods = load_stratified_methods()
        logger.info(f"Loaded {len(methods)} stratified methods")
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    # Generate LLM-Sim summaries
    llm_sim_summaries = []
    rule_summaries = []
    
    logger.info(f"Generating LLM-Sim summaries (timeout: {timeout_seconds}s)...")
    for i, method_data in enumerate(methods):
        if i % 10 == 0:
            logger.info(f"Processing method {i+1}/{len(methods)}")
        
        # Try LLM-Sim generation
        llm_sim_result = generate_llm_sim_summary(method_data, timeout_seconds)
        
        if llm_sim_result and llm_sim_result['success']:
            llm_sim_summaries.append(llm_sim_result)
        else:
            # Fallback to rule-based
            logger.info(f"LLM-Sim failed for {method_data.get('method_id')}, using rule-based fallback")
            rule_result = generate_rule_summary(method_data)
            if rule_result and rule_result['success']:
                rule_summaries.append(rule_result)
    
    # Generate rule-based summaries for any remaining methods (if needed)
    # Note: In this implementation, we only generate rule-based as fallback
    # If you want all methods to have rule-based summaries too, uncomment below:
    # logger.info("Generating rule-based summaries for all methods...")
    # for method_data in methods:
    #     rule_result = generate_rule_summary(method_data)
    #     if rule_result and rule_result['success']:
    #         rule_summaries.append(rule_result)
    
    # Save results
    logger.info(f"Saving {len(llm_sim_summaries)} LLM-Sim summaries...")
    save_summaries_to_csv(llm_sim_summaries, LLM_SIM_OUTPUT_PATH)
    
    logger.info(f"Saving {len(rule_summaries)} rule-based summaries...")
    save_summaries_to_csv(rule_summaries, RULE_SUMMARY_OUTPUT_PATH)
    
    # Log summary statistics
    total_methods = len(methods)
    llm_success = len(llm_sim_summaries)
    rule_success = len(rule_summaries)
    llm_failures = total_methods - llm_success
    
    logger.info("Summary generation complete:")
    logger.info(f"  Total methods processed: {total_methods}")
    logger.info(f"  LLM-Sim successful: {llm_success}")
    logger.info(f"  LLM-Sim failed (fallback to rule): {llm_failures}")
    logger.info(f"  Rule-based successful: {rule_success}")
    
    return {
        'total_methods': total_methods,
        'llm_sim_success': llm_success,
        'llm_sim_failures': llm_failures,
        'rule_success': rule_success,
        'output_files': [str(LLM_SIM_OUTPUT_PATH), str(RULE_SUMMARY_OUTPUT_PATH)]
    }

if __name__ == "__main__":
    setup_logging()
    result = main()
    logger.info(f"Final result: {json.dumps(result, indent=2)}")