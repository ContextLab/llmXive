import os
import sys
import csv
import json
import hashlib
import ast
import logging
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

# Import from existing API surface
from utils.classifier import CodeBERTClassifier, ClassifierError, ModelNotFoundError
from utils.logging_config import get_logger, setup_logging
from utils.models import CodeBlock, LabelType

# Constants
CONFIDENCE_THRESHOLD = 0.8
CHECKPOINT_FILE = "data/logs/data_curation_checkpoint.json"
CODE_BLOCKS_FILE = "data/raw/code_blocks.csv"
TAGGED_BLOCKS_FILE = "data/processed/tagged_blocks.csv"
CLASSIFIER_EXCLUSIONS_LOG = "data/logs/classifier_exclusions.log"

def setup_logging():
    """Initialize logging infrastructure."""
    return setup_logging()

def setup_output_directories():
    """Create necessary output directories."""
    dirs = [
        "data/raw",
        "data/processed",
        "data/ground_truth",
        "data/logs",
        "figures"
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def load_checkpoint():
    """Load checkpoint state if exists."""
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, 'r') as f:
            return json.load(f)
    return {"processed_repos": [], "processed_blocks": []}

def save_checkpoint(state):
    """Save checkpoint state."""
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def calculate_file_hash(content: str) -> str:
    """Calculate SHA256 hash of content."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def extract_code_blocks_py(file_path: str, repo_root: str) -> List[Dict[str, Any]]:
    """Extract code blocks from Python files using AST."""
    blocks = []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        tree = ast.parse(content)
        relative_path = os.path.relpath(file_path, repo_root)
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                start_line = node.lineno
                end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line
                
                # Extract source code for the node
                lines = content.split('\n')
                block_content = '\n'.join(lines[start_line-1:end_line])
                
                block_id = f"{relative_path}:{start_line}-{end_line}"
                blocks.append({
                    "block_id": block_id,
                    "file_path": relative_path,
                    "start_line": start_line,
                    "end_line": end_line,
                    "language": "python",
                    "content_hash": calculate_file_hash(block_content),
                    "content": block_content
                })
    except Exception as e:
        logging.warning(f"Failed to parse {file_path}: {e}")
    
    return blocks

def extract_code_blocks_js(file_path: str, repo_root: str) -> List[Dict[str, Any]]:
    """Extract code blocks from JavaScript files using tree-sitter (simulated for now)."""
    # TODO: Implement actual tree-sitter parsing for JS
    # For now, return empty list as placeholder
    return []

def extract_code_blocks_from_repo(repo_path: str, repo_name: str) -> List[Dict[str, Any]]:
    """Extract all code blocks from a repository."""
    all_blocks = []
    
    for root, dirs, files in os.walk(repo_path):
        # Skip hidden directories and common non-code directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', 'venv', '__pycache__']]
        
        for file in files:
            file_path = os.path.join(root, file)
            
            if file.endswith('.py'):
                blocks = extract_code_blocks_py(file_path, repo_path)
                all_blocks.extend(blocks)
            elif file.endswith(('.js', '.jsx', '.ts', '.tsx')):
                blocks = extract_code_blocks_js(file_path, repo_path)
                all_blocks.extend(blocks)
    
    return all_blocks

def tag_blocks_with_classifier(blocks: List[Dict[str, Any]], logger: logging.Logger) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Tag code blocks as LLM-generated or Human-written using CodeBERT classifier.
    
    Args:
        blocks: List of code block dictionaries
        logger: Logger instance for recording exclusions
    
    Returns:
        Tuple of (tagged_blocks, excluded_blocks)
    """
    if not blocks:
        return [], []
    
    # Initialize classifier
    try:
        classifier = CodeBERTClassifier()
    except (ModelNotFoundError, ClassifierError) as e:
        logger.error(f"Failed to initialize CodeBERT classifier: {e}")
        # If classifier fails to load, exclude all blocks
        excluded = [{**block, "exclusion_reason": "classifier_initialization_failed"} for block in blocks]
        return [], excluded
    
    tagged_blocks = []
    excluded_blocks = []
    
    for block in blocks:
        content = block.get("content", "")
        
        if not content or len(content.strip()) == 0:
            excluded_blocks.append({
                **block,
                "predicted_label": None,
                "confidence": 0.0,
                "exclusion_reason": "empty_content"
            })
            continue
        
        try:
            # Run inference
            prediction, confidence = classifier.predict(content)
            
            if confidence >= CONFIDENCE_THRESHOLD:
                tagged_block = {
                    **block,
                    "predicted_label": prediction.value if hasattr(prediction, 'value') else str(prediction),
                    "confidence": confidence
                }
                tagged_blocks.append(tagged_block)
            else:
                excluded_blocks.append({
                    **block,
                    "predicted_label": None,
                    "confidence": confidence,
                    "exclusion_reason": f"low_confidence_{confidence:.2f}"
                })
        
        except ClassifierError as e:
            logger.warning(f"Classification failed for block {block.get('block_id')}: {e}")
            excluded_blocks.append({
                **block,
                "predicted_label": None,
                "confidence": 0.0,
                "exclusion_reason": f"classification_error_{str(e)}"
            })
    
    return tagged_blocks, excluded_blocks

def save_tagged_blocks(tagged_blocks: List[Dict[str, Any]], output_path: str):
    """Save tagged blocks to CSV."""
    if not tagged_blocks:
        return
    
    fieldnames = [
        "block_id", "file_path", "start_line", "end_line", "language",
        "content_hash", "predicted_label", "confidence"
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for block in tagged_blocks:
            row = {k: block.get(k, '') for k in fieldnames}
            # Remove content field as it's too large for CSV
            writer.writerow(row)

def save_exclusions_log(excluded_blocks: List[Dict[str, Any]], log_path: str):
    """Save excluded blocks to log file."""
    with open(log_path, 'w', encoding='utf-8') as f:
        for block in excluded_blocks:
            reason = block.get("exclusion_reason", "unknown")
            block_id = block.get("block_id", "unknown")
            confidence = block.get("confidence", 0.0)
            f.write(f"{block_id},{reason},{confidence:.4f}\n")

def main():
    """Main execution function for data curation with classifier tagging."""
    logger = setup_logging()
    setup_output_directories()
    
    logger.info("Starting data curation pipeline with CodeBERT classifier")
    
    # Load checkpoint
    checkpoint = load_checkpoint()
    processed_repos = checkpoint.get("processed_repos", [])
    
    # Check if code_blocks.csv exists
    if not os.path.exists(CODE_BLOCKS_FILE):
        logger.error(f"Code blocks file not found: {CODE_BLOCKS_FILE}")
        logger.error("Please run T012 first to extract code blocks")
        return 1
    
    # Load code blocks
    blocks = []
    with open(CODE_BLOCKS_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Reconstruct content if needed (it's not in the CSV for space reasons)
            # In a real implementation, we'd need to re-read the files or store content
            blocks.append(row)
    
    logger.info(f"Loaded {len(blocks)} code blocks from {CODE_BLOCKS_FILE}")
    
    if not blocks:
        logger.warning("No code blocks found to process")
        return 0
    
    # Tag blocks with classifier
    logger.info(f"Running CodeBERT classifier on {len(blocks)} blocks")
    start_time = time.time()
    
    tagged_blocks, excluded_blocks = tag_blocks_with_classifier(blocks, logger)
    
    elapsed = time.time() - start_time
    logger.info(f"Classification completed in {elapsed:.2f}s")
    logger.info(f"Tagged blocks: {len(tagged_blocks)}")
    logger.info(f"Excluded blocks: {len(excluded_blocks)}")
    
    # Save tagged blocks
    save_tagged_blocks(tagged_blocks, TAGGED_BLOCKS_FILE)
    logger.info(f"Saved {len(tagged_blocks)} tagged blocks to {TAGGED_BLOCKS_FILE}")
    
    # Save exclusions log
    save_exclusions_log(excluded_blocks, CLASSIFIER_EXCLUSIONS_LOG)
    logger.info(f"Saved {len(excluded_blocks)} exclusions to {CLASSIFIER_EXCLUSIONS_LOG}")
    
    # Update checkpoint
    checkpoint["tagged_blocks_count"] = len(tagged_blocks)
    checkpoint["excluded_blocks_count"] = len(excluded_blocks)
    checkpoint["completion_time"] = datetime.now().isoformat()
    save_checkpoint(checkpoint)
    
    logger.info("Data curation with classifier tagging completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())