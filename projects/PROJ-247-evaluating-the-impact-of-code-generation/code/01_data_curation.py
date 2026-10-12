import os
import sys
import csv
import json
import hashlib
import ast
import logging
import subprocess
import argparse
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional, Tuple

from github import Github, GithubException
from dotenv import load_dotenv

# Import from local utils
from utils.logging_config import setup_project_logging
from utils.classifier import CodeBERTClassifier, ClassifierError

load_dotenv()

# Constants
CONFIDENCE_THRESHOLD = 0.8
BLOCKS_CSV_PATH = "data/raw/code_blocks.csv"
TAGGED_BLOCKS_CSV_PATH = "data/raw/code_blocks_tagged.csv"
EXCLUSIONS_LOG_PATH = "data/logs/classifier_exclusions.log"
REPO_LIST_CSV = "data/raw/repo_list.csv"
REPO_METADATA_CSV = "data/raw/repo_metadata.csv"
CLONES_DIR = "data/raw/clones"
CHECKPOINT_DIR = "data/logs/checkpoints"

def setup_logging():
    """Configure logging for the data curation pipeline."""
    return setup_project_logging("data_curation", "data/logs/data_curation.log")

def setup_output_directories():
    """Ensure all required output directories exist."""
    dirs = [
        "data/raw",
        "data/raw/clones",
        "data/processed",
        "data/ground_truth",
        "data/logs",
        "data/logs/checkpoints",
        "docs/paper",
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

def calculate_total_loc(repo_path: Path) -> int:
    """Calculate total lines of code for .py and .js files."""
    total_loc = 0
    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.endswith(('.py', '.js')):
                try:
                    with open(Path(root) / file, 'r', encoding='utf-8', errors='ignore') as f:
                        total_loc += sum(1 for _ in f)
                except Exception:
                    continue
    return total_loc

def curate_repositories(logger: logging.Logger):
    """
    FR-001: Identify and clone active Python/JS repositories.
    Filters: topic:llm-generated OR topic:copilot, stars >= 5, 1 commit/90 days.
    """
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        logger.error("GITHUB_TOKEN not found in environment.")
        sys.exit(1)

    g = Github(token)
    repos_found = []
    
    # Search queries
    queries = [
        'topic:llm-generated',
        'topic:copilot'
    ]
    # Keyword expansion if needed
    keyword_queries = [
        '"LLM generated code"',
        '"Copilot generated"'
    ]

    ninety_days_ago = datetime.now(timezone.utc) - timedelta(days=90)
    
    def process_query(query):
        nonlocal repos_found
        logger.info(f"Searching with query: {query}")
        try:
            results = g.search_repositories(query=query)
            for repo in results:
                if len(repos_found) >= 50:
                    break
                
                # Basic filters: stars >= 5 and activity (pushed_at is a reliable proxy for commit activity)
                if repo.stargazers_count >= 5 and repo.pushed_at and repo.pushed_at.replace(tzinfo=timezone.utc) >= ninety_days_ago:
                    # Avoid duplicates
                    if not any(r['repo_id'] == repo.id for r in repos_found):
                        repos_found.append({
                            "repo_id": repo.id,
                            "owner": repo.owner.login,
                            "name": repo.name,
                            "url": repo.clone_url,
                            "stargazers_count": repo.stargazers_count,
                            "created_at": repo.created_at.isoformat(),
                            "updated_at": repo.updated_at.isoformat(),
                        })
        except GithubException as e:
            logger.error(f"GitHub API error during search {query}: {e}")

    for q in queries:
        process_query(q)
    
    if len(repos_found) < 50:
        logger.info(f"Found only {len(repos_found)} repos, expanding search to keywords...")
        for q in keyword_queries:
            process_query(q)

    logger.info(f"Curation identified {len(repos_found)} repositories.")

    # Cloning and Metadata Extraction
    final_repo_list = []
    final_repo_metadata = []

    for repo_info in repos_found:
        repo_id = repo_info['repo_id']
        clone_url = repo_info['url']
        target_path = Path(CLONES_DIR) / f"{repo_info['owner']}_{repo_info['name']}"
        
        try:
            logger.info(f"Cloning {clone_url} to {target_path}...")
            subprocess.run(
                ["git", "clone", "--depth", "100", clone_url, str(target_path)],
                check=True, capture_output=True, text=True
            )
            
            loc = calculate_total_loc(target_path)
            
            final_repo_list.append({
                "repo_id": repo_id,
                "owner": repo_info['owner'],
                "name": repo_info['name'],
                "url": clone_url
            })
            
            final_repo_metadata.append({
                "repo_id": repo_id,
                "stargazers_count": repo_info['stargazers_count'],
                "created_at": repo_info['created_at'],
                "updated_at": repo_info['updated_at'],
                "total_loc": loc
            })
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to clone {clone_url}: {e.stderr}")
        except Exception as e:
            logger.error(f"Unexpected error cloning {clone_url}: {e}")

    # Save results
    with open(REPO_LIST_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["repo_id", "owner", "name", "url"])
        writer.writeheader()
        writer.writerows(final_repo_list)

    with open(REPO_METADATA_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["repo_id", "stargazers_count", "created_at", "updated_at", "total_loc"])
        writer.writeheader()
        writer.writerows(final_repo_metadata)

    logger.info(f"Saved curated list of {len(final_repo_list)} repos to {REPO_LIST_CSV} and {REPO_METADATA_CSV}")

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
    """Tag blocks using the CodeBERT classifier."""
    tagged = []
    excluded = []
    for block in blocks:
        try:
            content = block.get("content", "")
            if not content.strip(): continue
            res = classifier.predict(content)
            label = res['label']
            confidence = res['confidence']
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
        except Exception as e:
            logger.error(f"Classifier error: {e}")
            excluded.append({"block_id": block.get("block_id", "unknown"), "file_path": block.get("file_path", ""), "confidence": 0.0, "reason": str(e)})
    return tagged, excluded

def save_tagged_blocks(tagged_blocks: List[Dict[str, Any]], output_path: Path):
    if not tagged_blocks: return
    fieldnames = ["file_path", "start_line", "end_line", "language", "content_hash", "block_type", "predicted_label", "confidence"]
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(tagged_blocks)

def save_exclusions_log(excluded_blocks: List[Dict[str, Any]], output_path: Path, logger: logging.Logger):
    if not excluded_blocks: return
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["block_id", "file_path", "confidence", "reason"])
        writer.writeheader()
        writer.writerows(excluded_blocks)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--curate", action="store_true", help="Run repository curation (T002)")
    parser.add_argument("--tag", action="store_true", help="Run block tagging (T013)")
    args = parser.parse_args()

    logger = setup_logging()
    setup_output_directories()

    if args.curate:
        logger.info("Starting Repository Curation (T002)")
        curate_repositories(logger)
        logger.info("Repository Curation completed successfully.")

    if args.tag:
        logger.info("Starting Block Tagging (T013)")
        try:
            classifier = CodeBERTClassifier()
        except Exception as e:
            logger.critical(f"Classifier init failed: {e}")
            sys.exit(1)

        blocks_path = Path(BLOCKS_CSV_PATH)
        if not blocks_path.exists():
            logger.error(f"Blocks file not found at {blocks_path}. Run T003 first.")
            sys.exit(1)

        all_blocks = []
        with open(blocks_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                all_blocks.append({
                    "block_id": f"block_{i}",
                    "file_path": row.get("file_path", ""),
                    "start_line": int(row.get("start_line", 0)),
                    "end_line": int(row.get("end_line", 0)),
                    "language": row.get("language", ""),
                    "content_hash": row.get("content_hash", ""),
                    "content": row.get("content", "")
                })
        
        tagged, excluded = tag_blocks_with_classifier(all_blocks, classifier, logger)
        save_tagged_blocks(tagged, Path(TAGGED_BLOCKS_CSV_PATH))
        save_exclusions_log(excluded, Path(EXCLUSIONS_LOG_PATH), logger)
        logger.info("Block Tagging completed successfully.")

if __name__ == "__main__":
    main()