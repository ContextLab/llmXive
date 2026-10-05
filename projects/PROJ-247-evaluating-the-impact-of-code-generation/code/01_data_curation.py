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

# Import from local utils
from utils.logging_config import get_logger, setup_logging
from utils.classifier import CodeBERTClassifier, ClassifierError

# Constants
CONFIDENCE_THRESHOLD = 0.8
BLOCKS_CSV_PATH = "data/raw/code_blocks.csv"
TAGGED_BLOCKS_CSV_PATH = "data/raw/code_blocks_tagged.csv"
EXCLUSIONS_LOG_PATH = "data/logs/classifier_exclusions.log"
CHECKPOINT_DIR = "data/logs/checkpoints"

def setup_logging():
    """Configure logging for the data curation pipeline."""
    return setup_logging("data_curation", "data/logs/data_curation.log")

def setup_output_directories():
    """Ensure all required output directories exist."""
    dirs = [
        "data/raw",
        "data/processed",
        "data/ground_truth",
        "data/logs",
        "data/logs/checkpoints",
        "docs/paper",
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

def load_checkpoint(checkpoint_file: Path) -> List[Dict[str, Any]]:
    """Load progress from a checkpoint file."""
    if checkpoint_file.exists():
        with open(checkpoint_file, 'r') as f:
            return json.load(f)
    return []

def save_checkpoint(checkpoint_file: Path, data: List[Dict[str, Any]]):
    """Save progress to a checkpoint file."""
    with open(checkpoint_file, 'w') as f:
        json.dump(data, f, indent=2)

def calculate_file_hash(content: str) -> str:
    """Calculate SHA-256 hash of content."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def extract_code_blocks_py(file_path: Path) -> List[Dict[str, Any]]:
    """Extract code blocks (functions/classes) from a Python file using AST."""
    blocks = []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        tree = ast.parse(content)
        lines = content.splitlines()

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                start_line = node.lineno
                end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line
                block_content = '\n'.join(lines[start_line-1:end_line])
                blocks.append({
                    "file_path": str(file_path),
                    "start_line": start_line,
                    "end_line": end_line,
                    "language": "python",
                    "content": block_content,
                    "content_hash": calculate_file_hash(block_content),
                    "block_type": "class" if isinstance(node, ast.ClassDef) else "function"
                })
    except Exception as e:
        logging.getLogger(__name__).warning(f"Failed to parse {file_path}: {e}")
    return blocks

def extract_code_blocks_js(file_path: Path) -> List[Dict[str, Any]]:
    """Extract code blocks from a JS file. Placeholder for tree-sitter integration."""
    # For now, return empty or simple heuristic if tree-sitter not available
    # In a full implementation, this would use tree-sitter-acorn
    logging.getLogger(__name__).info(f"JS extraction not fully implemented for {file_path}")
    return []

def extract_code_blocks_from_repo(repo_path: Path) -> List[Dict[str, Any]]:
    """Extract code blocks from all Python and JS files in a repository."""
    all_blocks = []
    for root, _, files in os.walk(repo_path):
        for file in files:
            file_path = Path(root) / file
            if file.endswith('.py'):
                all_blocks.extend(extract_code_blocks_py(file_path))
            elif file.endswith('.js'):
                all_blocks.extend(extract_code_blocks_js(file_path))
    return all_blocks

def tag_blocks_with_classifier(blocks: List[Dict[str, Any]], classifier: CodeBERTClassifier, logger: logging.Logger) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Tag blocks using the CodeBERT classifier.
    Returns (tagged_blocks, excluded_blocks).
    Excludes blocks with confidence < CONFIDENCE_THRESHOLD.
    """
    tagged = []
    excluded = []

    for block in blocks:
        try:
            content = block.get("content", "")
            if not content.strip():
                continue

            # Run inference
            label, confidence = classifier.predict(content)

            if confidence >= CONFIDENCE_THRESHOLD:
                block["predicted_label"] = label.value if hasattr(label, 'value') else str(label)
                block["confidence"] = confidence
                tagged.append(block)
            else:
                excluded.append({
                    "block_id": block.get("block_id", "unknown"),
                    "file_path": block.get("file_path", ""),
                    "confidence": confidence,
                    "reason": f"confidence_below_threshold_{CONFIDENCE_THRESHOLD}"
                })
                logger.debug(f"Excluded block {block.get('block_id')}: confidence {confidence:.4f} < {CONFIDENCE_THRESHOLD}")

        except ClassifierError as e:
            logger.error(f"Classifier error for block in {block.get('file_path')}: {e}")
            excluded.append({
                "block_id": block.get("block_id", "unknown"),
                "file_path": block.get("file_path", ""),
                "confidence": 0.0,
                "reason": f"classifier_error_{str(e)}"
            })
        except Exception as e:
            logger.error(f"Unexpected error processing block in {block.get('file_path')}: {e}")
            excluded.append({
                "block_id": block.get("block_id", "unknown"),
                "file_path": block.get("file_path", ""),
                "confidence": 0.0,
                "reason": f"unexpected_error_{str(e)}"
            })

    return tagged, excluded

def save_tagged_blocks(tagged_blocks: List[Dict[str, Any]], output_path: Path):
    """Save tagged blocks to CSV."""
    if not tagged_blocks:
        logging.getLogger(__name__).warning("No tagged blocks to save.")
        return

    fieldnames = [
        "file_path", "start_line", "end_line", "language", "content_hash",
        "block_type", "predicted_label", "confidence"
    ]

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for block in tagged_blocks:
            writer.writerow(block)

def save_exclusions_log(excluded_blocks: List[Dict[str, Any]], output_path: Path, logger: logging.Logger):
    """Save exclusions log to file."""
    if not excluded_blocks:
        logger.info("No blocks were excluded.")
        return

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["block_id", "file_path", "confidence", "reason"])
        writer.writeheader()
        for entry in excluded_blocks:
            writer.writerow(entry)
    logger.info(f"Saved {len(excluded_blocks)} exclusions to {output_path}")

def main():
    """Main entry point for data curation pipeline including classifier tagging."""
    logger = setup_logging()
    setup_output_directories()

    logger.info("Starting Data Curation Pipeline with Classifier Integration (T013)")

    # Initialize Classifier
    try:
        classifier = CodeBERTClassifier()
        logger.info("CodeBERT Classifier initialized successfully.")
    except Exception as e:
        logger.critical(f"Failed to initialize classifier: {e}")
        sys.exit(1)

    # Load existing code blocks from T012
    blocks_path = Path(BLOCKS_CSV_PATH)
    if not blocks_path.exists():
        logger.error(f"Code blocks file not found at {blocks_path}. Please run T012 first.")
        sys.exit(1)

    all_blocks = []
    with open(blocks_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            # Reconstruct block object
            block = {
                "block_id": f"block_{i}",
                "file_path": row.get("file_path", ""),
                "start_line": int(row.get("start_line", 0)),
                "end_line": int(row.get("end_line", 0)),
                "language": row.get("language", ""),
                "content_hash": row.get("content_hash", ""),
                "content": row.get("content", "") # Ensure content is available
            }
            all_blocks.append(block)

    logger.info(f"Loaded {len(all_blocks)} code blocks from {blocks_path}")

    # Tag blocks
    tagged_blocks, excluded_blocks = tag_blocks_with_classifier(all_blocks, classifier, logger)

    # Save outputs
    tagged_output_path = Path(TAGGED_BLOCKS_CSV_PATH)
    save_tagged_blocks(tagged_blocks, tagged_output_path)
    logger.info(f"Saved {len(tagged_blocks)} tagged blocks to {tagged_output_path}")

    exclusions_output_path = Path(EXCLUSIONS_LOG_PATH)
    save_exclusions_log(excluded_blocks, exclusions_output_path, logger)

    logger.info("Data Curation Pipeline (T013) completed successfully.")

if __name__ == "__main__":
    main()