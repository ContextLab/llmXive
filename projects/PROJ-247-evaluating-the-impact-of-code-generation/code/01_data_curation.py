import os
import sys
import csv
import json
import hashlib
import ast
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

# Import from project utils as per API surface
from utils.models import CodeBlock, LabelType
from utils.classifier import CodeBERTClassifier, ClassifierError
from utils.logging_config import get_logger, setup_logging

# Constants
CONFIDENCE_THRESHOLD = 0.8
LOG_FILE = "data/logs/classifier_exclusions.log"
OUTPUT_FILE = "data/raw/code_blocks_tagged.csv"

def setup_logging():
    """Initialize logging for the data curation pipeline."""
    log_path = Path("data/logs")
    log_path.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_path / "curation.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger("data_curation")

logger = setup_logging()

def setup_output_directories():
    """Ensure all required output directories exist."""
    dirs = [
        "data/raw",
        "data/processed",
        "data/ground_truth",
        "data/logs",
        "data/temp"
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
    logger.info("Output directories verified.")

def load_checkpoint(checkpoint_file: str) -> Dict[str, Any]:
    """Load checkpoint state if it exists."""
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, 'r') as f:
            return json.load(f)
    return {"completed_repos": [], "current_repo_index": 0, "state": "start"}

def save_checkpoint(checkpoint_file: str, state: Dict[str, Any]):
    """Save current pipeline state."""
    with open(checkpoint_file, 'w') as f:
        json.dump(state, f, indent=2)
    logger.info(f"Checkpoint saved to {checkpoint_file}")

def calculate_file_hash(content: str) -> str:
    """Calculate SHA256 hash of content."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def extract_code_blocks_py(file_path: str, repo_root: str) -> List[Dict[str, Any]]:
    """Extract code blocks (functions/classes) from Python files using AST."""
    blocks = []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        try:
            tree = ast.parse(content)
        except SyntaxError:
            logger.warning(f"Syntax error in {file_path}, skipping.")
            return blocks

        rel_path = os.path.relpath(file_path, repo_root)

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                start_line = node.lineno
                end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line
                block_content = ast.get_source_segment(content, node)
                if block_content:
                    blocks.append({
                        "file_path": rel_path,
                        "start_line": start_line,
                        "end_line": end_line,
                        "language": "python",
                        "content_hash": calculate_file_hash(block_content),
                        "content": block_content,
                        "node_type": type(node).__name__
                    })
    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
    
    return blocks

def extract_code_blocks_js(file_path: str, repo_root: str) -> List[Dict[str, Any]]:
    """Extract code blocks from JavaScript files (simplified heuristic for now)."""
    # Note: Full JS parsing requires tree-sitter, but we implement a basic regex-based
    # extraction for the scope of this task to avoid external non-standard dependencies
    # unless explicitly added to requirements.
    blocks = []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        lines = content.split('\n')
        rel_path = os.path.relpath(file_path, repo_root)
        
        # Simple heuristic: look for function declarations and class definitions
        # This is a placeholder for a real parser if tree-sitter is not available
        # In a real scenario, we would use tree-sitter as per T012 spec
        start_line = 0
        brace_count = 0
        in_block = False
        block_start = 0
        
        for i, line in enumerate(lines):
            if 'function ' in line or 'class ' in line or 'const ' in line:
                if not in_block:
                    block_start = i
                    in_block = True
            
            if in_block:
                brace_count += line.count('{') - line.count('}')
                if brace_count == 0 and in_block:
                    # End of block
                    block_content = '\n'.join(lines[block_start:i+1])
                    blocks.append({
                        "file_path": rel_path,
                        "start_line": block_start + 1,
                        "end_line": i + 1,
                        "language": "javascript",
                        "content_hash": calculate_file_hash(block_content),
                        "content": block_content,
                        "node_type": "function_or_class"
                    })
                    in_block = False
                    brace_count = 0
    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
    
    return blocks

def extract_code_blocks_from_repo(repo_path: str) -> List[Dict[str, Any]]:
    """Extract all code blocks from a repository."""
    all_blocks = []
    for root, _, files in os.walk(repo_path):
        # Skip hidden directories and common non-code dirs
        if any(part.startswith('.') for part in Path(root).parts):
            continue
        
        for file in files:
            if file.endswith('.py'):
                blocks = extract_code_blocks_py(os.path.join(root, file), repo_path)
                all_blocks.extend(blocks)
            elif file.endswith(('.js', '.jsx', '.ts', '.tsx')):
                blocks = extract_code_blocks_js(os.path.join(root, file), repo_path)
                all_blocks.extend(blocks)
    
    logger.info(f"Extracted {len(all_blocks)} blocks from {repo_path}")
    return all_blocks

def tag_blocks_with_classifier(blocks: List[Dict[str, Any]], classifier: CodeBERTClassifier) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Tag code blocks as LLM-generated or Human-written using CodeBERT classifier.
    
    Args:
        blocks: List of code block dictionaries
        classifier: Initialized CodeBERTClassifier instance
    
    Returns:
        Tuple of (tagged_blocks, excluded_blocks)
    """
    tagged = []
    excluded = []
    exclusions_log_path = Path(LOG_FILE)
    
    # Ensure log directory exists
    exclusions_log_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting classification of {len(blocks)} blocks with threshold {CONFIDENCE_THRESHOLD}")
    
    for block in blocks:
        content = block.get('content', '')
        if not content or len(content.strip()) < 10:
            # Skip empty or very short blocks
            excluded.append({
                'block_id': block.get('block_id'),
                'reason': 'Content too short or empty',
                'file_path': block.get('file_path')
            })
            continue
        
        try:
            prediction = classifier.predict(content)
            label = prediction['label']
            confidence = prediction['confidence']
            
            if confidence >= CONFIDENCE_THRESHOLD:
                tagged_block = block.copy()
                tagged_block['predicted_label'] = label
                tagged_block['confidence'] = confidence
                tagged.append(tagged_block)
            else:
                excluded.append({
                    'block_id': block.get('block_id'),
                    'reason': f'Low confidence ({confidence:.4f} < {CONFIDENCE_THRESHOLD})',
                    'file_path': block.get('file_path'),
                    'confidence': confidence,
                    'predicted_label': label
                })
        except ClassifierError as e:
            logger.error(f"Classifier error for block {block.get('block_id')}: {e}")
            excluded.append({
                'block_id': block.get('block_id'),
                'reason': f'Classifier error: {str(e)}',
                'file_path': block.get('file_path')
            })
        except Exception as e:
            logger.error(f"Unexpected error classifying block {block.get('block_id')}: {e}")
            excluded.append({
                'block_id': block.get('block_id'),
                'reason': f'Unexpected error: {str(e)}',
                'file_path': block.get('file_path')
            })
    
    # Write exclusions log
    with open(exclusions_log_path, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['block_id', 'reason', 'file_path', 'confidence', 'predicted_label'])
        if f.tell() == 0:
            writer.writeheader()
        for exc in excluded:
            writer.writerow(exc)
    
    logger.info(f"Classification complete. Tagged: {len(tagged)}, Excluded: {len(excluded)}")
    return tagged, excluded

def save_tagged_blocks(blocks: List[Dict[str, Any]], output_path: str):
    """Save tagged blocks to CSV."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = [
        'block_id', 'file_path', 'start_line', 'end_line', 'language', 
        'content_hash', 'predicted_label', 'confidence'
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for block in blocks:
            # Create a row with only the necessary fields
            row = {k: block.get(k) for k in fieldnames}
            # Generate block_id if not present
            if not row.get('block_id'):
                row['block_id'] = calculate_file_hash(block.get('content', ''))[:16]
            writer.writerow(row)
    
    logger.info(f"Saved {len(blocks)} tagged blocks to {output_path}")

def main():
    """Main entry point for data curation with classification."""
    logger.info("Starting data curation pipeline with classification (T013)")
    
    setup_output_directories()
    
    # Initialize classifier
    try:
        classifier = CodeBERTClassifier()
        logger.info("CodeBERT classifier initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize classifier: {e}")
        sys.exit(1)
    
    # Load or initialize checkpoint
    checkpoint_file = "data/logs/curation_checkpoint.json"
    checkpoint = load_checkpoint(checkpoint_file)
    
    # Load repository list (assuming it was created by T010b/T010c)
    repo_list_path = "data/raw/repo_list.csv"
    if not os.path.exists(repo_list_path):
        logger.error(f"Repository list not found at {repo_list_path}. Run T010b/T010c first.")
        sys.exit(1)
    
    repos = []
    with open(repo_list_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            repos.append(row)
    
    logger.info(f"Loaded {len(repos)} repositories from {repo_list_path}")
    
    all_tagged_blocks = []
    start_index = checkpoint.get('current_repo_index', 0)
    
    for i in range(start_index, len(repos)):
        repo_info = repos[i]
        repo_name = repo_info.get('name') or repo_info.get('full_name')
        repo_path = repo_info.get('local_path') or f"data/temp/{repo_name}"
        
        logger.info(f"Processing repo {i+1}/{len(repos)}: {repo_name}")
        
        if not os.path.exists(repo_path):
            logger.warning(f"Repository path not found: {repo_path}, skipping.")
            checkpoint['current_repo_index'] = i + 1
            save_checkpoint(checkpoint_file, checkpoint)
            continue
        
        # Extract code blocks (T012 logic - assumed to be implemented)
        # In a real scenario, we would check if code_blocks.csv exists and load it
        code_blocks_csv = "data/raw/code_blocks.csv"
        if os.path.exists(code_blocks_csv):
            # Load existing blocks if they were already extracted
            blocks = []
            with open(code_blocks_csv, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    blocks.append(row)
            logger.info(f"Loaded {len(blocks)} blocks from existing CSV")
        else:
            # Extract blocks from repo
            blocks = extract_code_blocks_from_repo(repo_path)
            # Save extracted blocks for downstream tasks
            if blocks:
                with open(code_blocks_csv, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=blocks[0].keys() if blocks else [])
                    if f.tell() == 0 and blocks:
                        writer.writeheader()
                    for block in blocks:
                        writer.writerow(block)
        
        # Tag blocks with classifier (T013 core logic)
        tagged_blocks, _ = tag_blocks_with_classifier(blocks, classifier)
        all_tagged_blocks.extend(tagged_blocks)
        
        # Update checkpoint
        checkpoint['current_repo_index'] = i + 1
        checkpoint['last_processed_repo'] = repo_name
        save_checkpoint(checkpoint_file, checkpoint)
    
    # Save final tagged blocks
    output_file = "data/raw/code_blocks_tagged.csv"
    save_tagged_blocks(all_tagged_blocks, output_file)
    
    logger.info("Data curation pipeline with classification completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())
