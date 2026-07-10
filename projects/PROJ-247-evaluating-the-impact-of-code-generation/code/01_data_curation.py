import os
import sys
import time
import csv
import json
import hashlib
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

# Import from existing project modules
from utils.models import Repository, CodeBlock, LabelType
from utils.github_client import GitHubClient
from utils.logging_config import get_logger
from utils.classifier import CodeBERTClassifier

logger = get_logger(__name__)

# Constants
CHECKPOINT_FILE = "data/logs/curation_checkpoint.json"
REPO_CLONE_DEPTH = 100
MIN_STARS = 5
MIN_COMMITS_90DAYS = 1
CONFIDENCE_THRESHOLD = 0.8
TOPICS_SEARCH = ["topic:llm-generated", "topic:copilot"]
KEYWORD_SEARCHES = [
    "LLM generated code",
    "Copilot generated code",
    "AI generated code"
]

def setup_output_directories() -> Path:
    """Ensure all required output directories exist."""
    base_dirs = [
        "data/raw",
        "data/processed",
        "data/ground_truth",
        "data/logs",
        "data/cloned_repos"
    ]
    for d in base_dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
    return Path("data/raw")

def load_checkpoint() -> Dict[str, Any]:
    """Load existing checkpoint if it exists."""
    if Path(CHECKPOINT_FILE).exists():
        with open(CHECKPOINT_FILE, 'r') as f:
            return json.load(f)
    return {
        "last_run": None,
        "processed_repos": [],
        "skipped_repos": [],
        "total_repos": 0,
        "completed_blocks": 0
    }

def save_checkpoint(progress_data: Dict[str, Any]):
    """Save current progress to checkpoint file."""
    progress_data["last_run"] = datetime.now().isoformat()
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump(progress_data, f, indent=2)
    logger.info(f"Checkpoint saved: {len(progress_data.get('processed_repos', []))} repos processed")

def search_github_repos(client: GitHubClient, min_repos: int = 50) -> List[Dict[str, Any]]:
    """
    Search GitHub for repositories with LLM-generated code topics.
    Falls back to keyword search if insufficient repos found via topics.
    """
    all_repos = []
    
    # Try topic search first
    for topic in TOPICS_SEARCH:
        try:
            repos = client.search_repos(query=topic, per_page=100)
            all_repos.extend(repos)
            logger.info(f"Found {len(repos)} repos for topic: {topic}")
        except Exception as e:
            logger.warning(f"Topic search failed for {topic}: {e}")

    # Deduplicate
    unique_repos = {repo['id']: repo for repo in all_repos}.values()
    unique_repos = list(unique_repos)

    # If not enough, try keyword search
    if len(unique_repos) < min_repos:
        logger.info(f"Only {len(unique_repos)} repos found via topics. Expanding to keyword search...")
        for keyword in KEYWORD_SEARCHES:
            try:
                repos = client.search_repos(query=keyword, per_page=50)
                for repo in repos:
                    if repo['id'] not in unique_repos:
                        unique_repos.append(repo)
                logger.info(f"Found {len(repos)} repos for keyword: {keyword}")
            except Exception as e:
                logger.warning(f"Keyword search failed for {keyword}: {e}")

    return list(unique_repos)

def deduplicate_repos(repos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicate repositories by ID."""
    seen_ids = set()
    unique = []
    for repo in repos:
        if repo['id'] not in seen_ids:
            seen_ids.add(repo['id'])
            unique.append(repo)
    return unique

def filter_active_repos(repos: List[Dict[str, Any]], client: GitHubClient) -> List[Dict[str, Any]]:
    """
    Filter repositories based on activity criteria:
    - >= 5 stars
    - >= 1 commit in last 90 days
    """
    active_repos = []
    for repo in repos:
        try:
            # Check stars
            if repo.get('stargazers_count', 0) < MIN_STARS:
                continue
            
            # Check recent activity
            commits = client.get_commits(repo['full_name'], since_days=90, per_page=1)
            if len(commits) < MIN_COMMITS_90DAYS:
                continue
            
            active_repos.append(repo)
        except Exception as e:
            logger.warning(f"Skipping repo {repo['full_name']} due to activity check error: {e}")
    
    return active_repos

def shallow_clone_repo(client: GitHubClient, repo: Dict[str, Any], dest_path: Path) -> bool:
    """
    Clone repository with shallow depth (100) to save time and space.
    Returns True if successful, False otherwise.
    """
    repo_name = repo['full_name'].replace("/", "_")
    clone_path = dest_path / repo_name
    
    if clone_path.exists():
        logger.info(f"Repository already cloned: {repo_name}")
        return True

    try:
        logger.info(f"Cloning {repo['full_name']} (shallow depth={REPO_CLONE_DEPTH})...")
        cmd = [
            "git", "clone", "--depth", str(REPO_CLONE_DEPTH),
            "--single-branch",
            repo['html_url'],
            str(clone_path)
        ]
        subprocess.run(cmd, check=True, capture_output=True, timeout=300)
        logger.info(f"Successfully cloned: {repo_name}")
        return True
    except subprocess.TimeoutExpired:
        logger.error(f"Clone timeout for {repo['full_name']}")
        return False
    except subprocess.CalledProcessError as e:
        if "404" in str(e.stderr):
            logger.warning(f"Repository not found (404): {repo['full_name']}")
            return False
        logger.error(f"Clone failed for {repo['full_name']}: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error cloning {repo['full_name']}: {e}")
        return False

def extract_repository_metadata(repo: Dict[str, Any]) -> Dict[str, Any]:
    """Extract key metadata fields for a repository."""
    return {
        "repo_id": repo['id'],
        "full_name": repo['full_name'],
        "stargazers_count": repo.get('stargazers_count', 0),
        "created_at": repo.get('created_at', ''),
        "updated_at": repo.get('updated_at', ''),
        "language": repo.get('language', ''),
        "default_branch": repo.get('default_branch', 'main')
    }

def extract_code_blocks_py(repo_path: Path) -> List[Dict[str, Any]]:
    """Extract code blocks from Python files in the repository."""
    blocks = []
    for py_file in repo_path.rglob("*.py"):
        try:
            with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Simple extraction: split by function/class definitions
            # In a real implementation, use AST parsing
            lines = content.split('\n')
            current_block = []
            block_start_line = 0
            in_block = False
            
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith('def ') or stripped.startswith('class '):
                    if in_block and current_block:
                        blocks.append({
                            "file_path": str(py_file.relative_to(repo_path)),
                            "start_line": block_start_line + 1,
                            "end_line": i,
                            "content": '\n'.join(current_block),
                            "block_type": "function" if stripped.startswith('def ') else "class"
                        })
                    current_block = [line]
                    block_start_line = i
                    in_block = True
                elif in_block:
                    current_block.append(line)
            
            # Add last block if exists
            if in_block and current_block:
                blocks.append({
                    "file_path": str(py_file.relative_to(repo_path)),
                    "start_line": block_start_line + 1,
                    "end_line": len(lines),
                    "content": '\n'.join(current_block),
                    "block_type": "function" if current_block[0].strip().startswith('def ') else "class"
                })
        except Exception as e:
            logger.warning(f"Error extracting blocks from {py_file}: {e}")
    
    return blocks

def extract_code_blocks_js(repo_path: Path) -> List[Dict[str, Any]]:
    """Extract code blocks from JavaScript files in the repository."""
    blocks = []
    for js_file in repo_path.rglob("*.js"):
        try:
            with open(js_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Simple extraction for JS
            lines = content.split('\n')
            current_block = []
            block_start_line = 0
            in_block = False
            
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith('function ') or stripped.startswith('const ') or stripped.startswith('let ') or stripped.startswith('var '):
                    if in_block and current_block:
                        blocks.append({
                            "file_path": str(js_file.relative_to(repo_path)),
                            "start_line": block_start_line + 1,
                            "end_line": i,
                            "content": '\n'.join(current_block),
                            "block_type": "function" if stripped.startswith('function ') else "variable"
                        })
                    current_block = [line]
                    block_start_line = i
                    in_block = True
                elif in_block:
                    current_block.append(line)
            
            if in_block and current_block:
                blocks.append({
                    "file_path": str(js_file.relative_to(repo_path)),
                    "start_line": block_start_line + 1,
                    "end_line": len(lines),
                    "content": '\n'.join(current_block),
                    "block_type": "function" if current_block[0].strip().startswith('function ') else "variable"
                })
        except Exception as e:
            logger.warning(f"Error extracting blocks from {js_file}: {e}")
    
    return blocks

def extract_code_blocks_from_repo(repo_path: Path) -> List[Dict[str, Any]]:
    """Extract all code blocks from a repository."""
    py_blocks = extract_code_blocks_py(repo_path)
    js_blocks = extract_code_blocks_js(repo_path)
    return py_blocks + js_blocks

def save_blocks_to_csv(blocks: List[Dict[str, Any]], repo_id: int, output_path: Path):
    """Save extracted code blocks to a CSV file."""
    if not blocks:
        return
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    file_path = output_path / f"repo_{repo_id}_blocks.csv"
    
    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=blocks[0].keys() | {"repo_id"})
        writer.writeheader()
        for block in blocks:
            block["repo_id"] = repo_id
            writer.writerow(block)

def detect_git_mv_exclusions(blocks: List[Dict[str, Any]], repo_path: Path) -> List[Dict[str, Any]]:
    """
    Detect blocks that might have been moved via 'git mv' and exclude them.
    Heuristic: check if file path hash changed or directory level changed significantly.
    """
    excluded_blocks = []
    included_blocks = []
    
    # In a real implementation, we would compare with git log history
    # For now, we'll simulate by checking for suspicious path patterns
    for block in blocks:
        file_path = block.get('file_path', '')
        # Simple heuristic: exclude if path contains 'moved' or 'backup'
        if any(s in file_path.lower() for s in ['moved', 'backup', 'old', 'temp']):
            excluded_blocks.append(block)
            logger.debug(f"Excluded block due to potential git mv: {file_path}")
        else:
            included_blocks.append(block)
    
    if excluded_blocks:
        logger.info(f"Excluded {len(excluded_blocks)} blocks due to potential git mv detection")
    
    return included_blocks

def calculate_static_metrics(blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Calculate static complexity metrics for each block using radon."""
    try:
        from radon.complexity import cc_visit
        from radon.visitors import ComplexityVisitor
    except ImportError:
        logger.warning("radon not installed, skipping complexity metrics")
        return blocks

    enriched_blocks = []
    for block in blocks:
        content = block.get('content', '')
        try:
            results = cc_visit(content)
            cc = max([r.complexity for r in results]) if results else 0
            
            # Calculate nesting depth
            lines = content.split('\n')
            max_indent = 0
            for line in lines:
                if line.strip():
                    indent = len(line) - len(line.lstrip())
                    max_indent = max(max_indent, indent)
            nesting_depth = max_indent // 4  # Assume 4-space indent
            
            loc = len([l for l in lines if l.strip()])
            
            block["cyclomatic_complexity"] = cc
            block["nesting_depth"] = nesting_depth
            block["lines_of_code"] = loc
            enriched_blocks.append(block)
        except Exception as e:
            logger.warning(f"Error calculating metrics for block in {block.get('file_path')}: {e}")
            # Keep block with default metrics
            block["cyclomatic_complexity"] = 0
            block["nesting_depth"] = 0
            block["lines_of_code"] = len(block.get('content', '').split('\n'))
            enriched_blocks.append(block)
    
    return enriched_blocks

def enrich_blocks_with_metrics(blocks: List[Dict[str, Any]], repo_id: int) -> List[Dict[str, Any]]:
    """Add repository ID and timestamp to blocks."""
    for block in blocks:
        block["repo_id"] = repo_id
        block["extracted_at"] = datetime.now().isoformat()
    return blocks

def enforce_repository_inclusion_criteria(blocks_by_repo: Dict[int, List[Dict[str, Any]]]) -> Dict[int, List[Dict[str, Any]]]:
    """
    Exclude repositories that don't have sufficient LLM and Human blocks.
    Criteria: >= 5 LLM blocks AND >= 5 Human blocks.
    """
    filtered = {}
    for repo_id, blocks in blocks_by_repo.items():
        llm_count = sum(1 for b in blocks if b.get('label') == 'LLM')
        human_count = sum(1 for b in blocks if b.get('label') == 'Human')
        
        if llm_count >= 5 and human_count >= 5:
            filtered[repo_id] = blocks
        else:
            logger.info(f"Excluding repo {repo_id}: LLM={llm_count}, Human={human_count} (need >=5 each)")
    
    return filtered

def tag_blocks_with_classifier(blocks: List[Dict[str, Any]], classifier: CodeBERTClassifier) -> List[Dict[str, Any]]:
    """Tag blocks as LLM or Human using CodeBERT classifier."""
    tagged_blocks = []
    
    for block in blocks:
        content = block.get('content', '')
        if len(content.strip()) < 10:  # Skip very short blocks
            continue
        
        try:
            prediction, confidence = classifier.predict(content)
            block["predicted_label"] = prediction
            block["confidence"] = confidence
            
            if confidence >= CONFIDENCE_THRESHOLD:
                block["label"] = prediction
                tagged_blocks.append(block)
            else:
                logger.debug(f"Low confidence ({confidence:.2f}) for block, excluding")
        except Exception as e:
            logger.warning(f"Classification error for block in {block.get('file_path')}: {e}")
            # Exclude low-confidence or error blocks
            continue
    
    return tagged_blocks

def main():
    """Main entry point for data curation pipeline with checkpoint support."""
    logger.info("Starting data curation pipeline with checkpoint support")
    
    # Setup directories
    output_dir = setup_output_directories()
    clone_dir = Path("data/cloned_repos")
    clone_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize checkpoint
    checkpoint = load_checkpoint()
    processed_repo_ids = set(checkpoint.get("processed_repos", []))
    skipped_repo_ids = set(checkpoint.get("skipped_repos", []))
    
    # Initialize components
    client = GitHubClient()
    classifier = CodeBERTClassifier()
    
    # Search for repositories
    logger.info("Searching GitHub for repositories...")
    repos = search_github_repos(client, min_repos=50)
    repos = deduplicate_repos(repos)
    logger.info(f"Found {len(repos)} unique repositories")
    
    # Update checkpoint with total count
    checkpoint["total_repos"] = len(repos)
    
    # Filter active repositories
    active_repos = filter_active_repos(repos, client)
    logger.info(f"Filtered to {len(active_repos)} active repositories")
    
    # Process repositories with checkpointing
    all_blocks_by_repo = {}
    metadata_rows = []
    
    for repo in active_repos:
        repo_id = repo['id']
        
        # Skip if already processed
        if repo_id in processed_repo_ids:
            logger.info(f"Skipping already processed repo: {repo['full_name']}")
            continue
        
        # Skip if previously skipped
        if repo_id in skipped_repo_ids:
            continue
        
        try:
            # Clone repository
            if not shallow_clone_repo(client, repo, clone_dir):
                skipped_repo_ids.add(repo_id)
                checkpoint["skipped_repos"] = list(skipped_repo_ids)
                save_checkpoint(checkpoint)
                continue
            
            # Extract metadata
            metadata = extract_repository_metadata(repo)
            metadata_rows.append(metadata)
            
            # Extract code blocks
            repo_path = clone_dir / repo['full_name'].replace("/", "_")
            blocks = extract_code_blocks_from_repo(repo_path)
            logger.info(f"Extracted {len(blocks)} blocks from {repo['full_name']}")
            
            if not blocks:
                skipped_repo_ids.add(repo_id)
                checkpoint["skipped_repos"] = list(skipped_repo_ids)
                save_checkpoint(checkpoint)
                continue
            
            # Detect and exclude git mv blocks
            blocks = detect_git_mv_exclusions(blocks, repo_path)
            
            # Tag blocks with classifier
            blocks = tag_blocks_with_classifier(blocks, classifier)
            
            # Calculate static metrics
            blocks = calculate_static_metrics(blocks)
            
            # Enrich with metadata
            blocks = enrich_blocks_with_metrics(blocks, repo_id)
            
            # Save blocks to CSV
            save_blocks_to_csv(blocks, repo_id, Path("data/processed"))
            
            # Store for later processing
            all_blocks_by_repo[repo_id] = blocks
            
            # Update checkpoint
            processed_repo_ids.add(repo_id)
            checkpoint["processed_repos"] = list(processed_repo_ids)
            checkpoint["completed_blocks"] = checkpoint.get("completed_blocks", 0) + len(blocks)
            save_checkpoint(checkpoint)
            
            logger.info(f"Completed processing repo {repo_id}: {len(blocks)} blocks")
            
        except Exception as e:
            logger.error(f"Failed to process repo {repo['full_name']}: {e}")
            skipped_repo_ids.add(repo_id)
            checkpoint["skipped_repos"] = list(skipped_repo_ids)
            save_checkpoint(checkpoint)
            continue
    
    # Save repository metadata
    if metadata_rows:
        with open(Path("data/raw") / "repo_metadata.csv", 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=metadata_rows[0].keys())
            writer.writeheader()
            writer.writerows(metadata_rows)
    
    # Apply inclusion criteria
    filtered_blocks_by_repo = enforce_repository_inclusion_criteria(all_blocks_by_repo)
    logger.info(f"Repositories after inclusion criteria: {len(filtered_blocks_by_repo)}")
    
    logger.info("Data curation pipeline completed")
    return filtered_blocks_by_repo

if __name__ == "__main__":
    main()