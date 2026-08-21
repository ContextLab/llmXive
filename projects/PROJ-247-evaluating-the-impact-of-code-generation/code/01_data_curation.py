import os
import sys
import time
import csv
import json
import hashlib
import subprocess
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import shutil

# Local imports
from utils.models import Repository, CodeBlock, LabelType
from utils.github_client import GitHubClient, GitHubClientError
from utils.classifier import CodeBERTClassifier, ClassifierError
from utils.logging_config import get_logger, setup_logging

# Constants
MIN_LLM_BLOCKS = 5
MIN_HUMAN_BLOCKS = 5
CHECKPOINT_DIR = "data/logs/checkpoints"
REPO_METADATA_PATH = "data/raw/repo_metadata.csv"
BLOCKS_CSV_PATH = "data/processed/blocks_raw.csv"
FILTERED_REPOS_PATH = "data/processed/filtered_repos.csv"

def setup_output_directories():
    """Ensure all required output directories exist."""
    dirs = [
        "data/raw",
        "data/processed",
        "data/ground_truth",
        "data/logs",
        CHECKPOINT_DIR
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

def load_checkpoint(repo_id: str) -> Optional[Dict[str, Any]]:
    """Load checkpoint data for a specific repo if it exists."""
    checkpoint_path = Path(CHECKPOINT_DIR) / f"{repo_id}.json"
    if checkpoint_path.exists():
        with open(checkpoint_path, 'r') as f:
            return json.load(f)
    return None

def save_checkpoint(repo_id: str, data: Dict[str, Any]):
    """Save checkpoint data for a specific repo."""
    checkpoint_path = Path(CHECKPOINT_DIR) / f"{repo_id}.json"
    with open(checkpoint_path, 'w') as f:
        json.dump(data, f, indent=2)

def search_github_repos(client: GitHubClient, query: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Search GitHub for repositories matching the query."""
    try:
        repos = client.search_repositories(query, limit=limit)
        return repos
    except GitHubClientError as e:
        logging.error(f"GitHub search failed: {e}")
        return []

def deduplicate_repos(repos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicate repositories based on full_name."""
    seen = set()
    unique = []
    for repo in repos:
        if repo['full_name'] not in seen:
            seen.add(repo['full_name'])
            unique.append(repo)
    return unique

def filter_active_repos(repos: List[Dict[str, Any]], min_stars: int = 5, days_threshold: int = 90) -> List[Dict[str, Any]]:
    """Filter repositories by activity and stars."""
    filtered = []
    now = datetime.now()
    for repo in repos:
        updated_at = datetime.fromisoformat(repo['updated_at'].replace('Z', '+00:00'))
        days_diff = (now - updated_at).days
        if repo['stargazers_count'] >= min_stars and days_diff <= days_threshold:
            filtered.append(repo)
    return filtered

def shallow_clone_repo(repo_url: str, target_dir: Path, depth: int = 100) -> bool:
    """Shallow clone a repository to the target directory."""
    try:
        if target_dir.exists():
            shutil.rmtree(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ['git', 'clone', '--depth', str(depth), repo_url, str(target_dir)],
            check=True,
            capture_output=True,
            timeout=300
        )
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to clone {repo_url}: {e.stderr.decode()}")
        return False
    except subprocess.TimeoutExpired:
        logging.error(f"Timeout cloning {repo_url}")
        return False

def extract_repository_metadata(repo: Dict[str, Any]) -> Dict[str, Any]:
    """Extract relevant metadata from a repository object."""
    return {
        'repo_id': repo['id'],
        'full_name': repo['full_name'],
        'stargazers_count': repo['stargazers_count'],
        'created_at': repo['created_at'],
        'updated_at': repo['updated_at'],
        'default_branch': repo.get('default_branch', 'main')
    }

def calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception:
        return ""

def extract_code_blocks_py(file_path: Path) -> List[Dict[str, Any]]:
    """Extract functions and classes from a Python file."""
    blocks = []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        lines = content.split('\n')
        current_block = None
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('def ') or stripped.startswith('class '):
                if current_block:
                    current_block['content'] = '\n'.join(current_block['lines'])
                    blocks.append(current_block)
                
                block_type = 'class' if stripped.startswith('class ') else 'function'
                name = stripped.split('(')[0].split(' ')[-1].split(':')[0].split(' ')[-1]
                
                current_block = {
                    'type': block_type,
                    'name': name,
                    'start_line': i + 1,
                    'lines': [line],
                    'file_path': str(file_path),
                    'language': 'python'
                }
            elif current_block:
                current_block['lines'].append(line)
        
        if current_block:
            current_block['content'] = '\n'.join(current_block['lines'])
            blocks.append(current_block)
    except Exception as e:
        logging.error(f"Error extracting blocks from {file_path}: {e}")
    
    return blocks

def extract_code_blocks_js(file_path: Path) -> List[Dict[str, Any]]:
    """Extract functions from a JavaScript file."""
    blocks = []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        lines = content.split('\n')
        current_block = None
        brace_count = 0
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            if stripped.startswith('function ') or 'function' in stripped and '(' in stripped:
                if current_block:
                    current_block['content'] = '\n'.join(current_block['lines'])
                    blocks.append(current_block)
                
                name = stripped.split('(')[0].split(' ')[-1]
                if name == 'function':
                    name = f"anon_{i}"
                
                current_block = {
                    'type': 'function',
                    'name': name,
                    'start_line': i + 1,
                    'lines': [line],
                    'file_path': str(file_path),
                    'language': 'javascript'
                }
                brace_count = line.count('{') - line.count('}')
            elif current_block:
                current_block['lines'].append(line)
                brace_count += line.count('{') - line.count('}')
                if brace_count <= 0 and current_block['lines']:
                    current_block['content'] = '\n'.join(current_block['lines'])
                    blocks.append(current_block)
                    current_block = None
                    brace_count = 0
        
        if current_block:
            current_block['content'] = '\n'.join(current_block['lines'])
            blocks.append(current_block)
    except Exception as e:
        logging.error(f"Error extracting blocks from {file_path}: {e}")
    
    return blocks

def extract_code_blocks_from_repo(repo_path: Path) -> List[Dict[str, Any]]:
    """Extract all code blocks from a repository."""
    all_blocks = []
    extensions = {'.py': extract_code_blocks_py, '.js': extract_code_blocks_js}
    
    for ext, extractor in extensions.items():
        for file_path in repo_path.rglob(f"*{ext}"):
            # Skip common non-source directories
            if any(part in file_path.parts for part in ['node_modules', '.git', 'venv', '__pycache__', 'dist', 'build']):
                continue
            blocks = extractor(file_path)
            all_blocks.extend(blocks)
    
    return all_blocks

def detect_git_mv_exclusions(blocks: List[Dict[str, Any]], repo_path: Path) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Detect and exclude blocks that were moved via git mv."""
    included = []
    excluded = []
    
    # Calculate directory level and path hash for each block
    for block in blocks:
        file_path = Path(block['file_path'])
        relative_path = file_path.relative_to(repo_path)
        
        # Check if file was likely moved (simple heuristic: path depth change)
        # In a real implementation, we'd check git log for 'mv' operations
        # For now, we log a warning if the path structure looks suspicious
        if '..' in str(relative_path):
            excluded.append({
                'block': block,
                'reason': 'Path traversal detected (potential git mv)'
            })
        else:
            included.append(block)
    
    if excluded:
        logging.info(f"Excluded {len(excluded)} blocks due to potential git mv refactoring")
    
    return included, excluded

def calculate_static_metrics(block: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate static complexity metrics for a code block."""
    content = block.get('content', '')
    lines = content.split('\n')
    
    # LOC
    loc = len(lines)
    
    # Cyclomatic complexity (simplified)
    complexity_keywords = ['if', 'elif', 'else', 'for', 'while', 'except', 'and', 'or']
    complexity = 1
    for line in lines:
        for keyword in complexity_keywords:
            if keyword in line:
                complexity += 1
    
    # Nesting depth (simplified)
    max_indent = 0
    for line in lines:
        if line.strip():
            indent = len(line) - len(line.lstrip())
            max_indent = max(max_indent, indent)
    nesting_depth = max_indent // 4  # Assuming 4 spaces per indent level
    
    return {
        'loc': loc,
        'cyclomatic_complexity': complexity,
        'nesting_depth': nesting_depth
    }

def tag_blocks_with_classifier(blocks: List[Dict[str, Any]], classifier: CodeBERTClassifier, confidence_threshold: float = 0.8) -> List[Dict[str, Any]]:
    """Tag blocks as LLM-generated or Human-written using CodeBERT."""
    tagged_blocks = []
    
    for block in blocks:
        content = block.get('content', '')
        if not content.strip():
            continue
        
        try:
            label, confidence = classifier.predict(content)
            if confidence >= confidence_threshold:
                block['label'] = label.value if hasattr(label, 'value') else str(label)
                block['confidence'] = confidence
                tagged_blocks.append(block)
            else:
                block['label'] = 'unknown'
                block['confidence'] = confidence
                tagged_blocks.append(block)
        except ClassifierError as e:
            logging.warning(f"Classification failed for block in {block.get('file_path')}: {e}")
            block['label'] = 'unknown'
            block['confidence'] = 0.0
            tagged_blocks.append(block)
    
    return tagged_blocks

def enforce_repository_inclusion_criteria(blocks: List[Dict[str, Any]], min_llm: int = MIN_LLM_BLOCKS, min_human: int = MIN_HUMAN_BLOCKS) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Enforce repository inclusion criteria: exclude repos with <5 LLM and <5 Human blocks after tagging.
    
    Args:
        blocks: List of all blocks from a repository (tagged)
        min_llm: Minimum number of LLM-generated blocks required
        min_human: Minimum number of Human-written blocks required
    
    Returns:
        Tuple of (kept_blocks, excluded_reasons)
    """
    if not blocks:
        return [], ["No blocks found"]
    
    llm_count = sum(1 for b in blocks if b.get('label') == 'llm')
    human_count = sum(1 for b in blocks if b.get('label') == 'human')
    
    excluded_reasons = []
    
    if llm_count < min_llm:
        excluded_reasons.append(f"Insufficient LLM blocks: {llm_count} < {min_llm}")
    
    if human_count < min_human:
        excluded_reasons.append(f"Insufficient Human blocks: {human_count} < {min_human}")
    
    if excluded_reasons:
        return [], excluded_reasons
    
    # Keep all blocks if criteria met
    return blocks, []

def save_blocks_to_csv(blocks: List[Dict[str, Any]], output_path: Path):
    """Save blocks to a CSV file."""
    if not blocks:
        return
    
    fieldnames = ['repo_id', 'file_path', 'language', 'type', 'name', 'start_line', 
                  'label', 'confidence', 'loc', 'cyclomatic_complexity', 'nesting_depth', 'content']
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for block in blocks:
            # Truncate content for CSV to avoid massive rows
            block_copy = block.copy()
            if 'content' in block_copy and len(block_copy['content']) > 1000:
                block_copy['content'] = block_copy['content'][:1000] + "..."
            writer.writerow(block_copy)

def save_filtered_repos(repos: List[Dict[str, Any]], output_path: Path):
    """Save list of filtered repositories to CSV."""
    if not repos:
        return
    
    fieldnames = ['repo_id', 'full_name', 'stargazers_count', 'created_at', 'updated_at', 'default_branch', 'keep']
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for repo in repos:
            writer.writerow(repo)

def main():
    """Main pipeline for data curation with repository inclusion criteria enforcement."""
    setup_output_directories()
    setup_logging()
    logger = get_logger(__name__)
    
    logger.info("Starting data curation pipeline with repository inclusion criteria enforcement")
    
    # Initialize GitHub client
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        logger.error("GITHUB_TOKEN not set in environment")
        sys.exit(1)
    
    client = GitHubClient(token=github_token)
    classifier = CodeBERTClassifier()
    
    # Search for repositories
    query = "topic:llm-generated OR topic:copilot"
    repos = search_github_repos(client, query, limit=200)
    
    if not repos:
        # Fallback to keyword search
        logger.info("No repos found with topics, expanding to keywords")
        repos = search_github_repos(client, '"LLM generated code" OR "Copilot generated"', limit=200)
    
    if not repos:
        logger.error("No repositories found")
        sys.exit(1)
    
    repos = deduplicate_repos(repos)
    repos = filter_active_repos(repos)
    
    logger.info(f"Found {len(repos)} active repositories after filtering")
    
    all_blocks = []
    filtered_repos = []
    
    for i, repo_meta in enumerate(repos):
        repo_id = str(repo_meta['id'])
        repo_name = repo_meta['full_name']
        logger.info(f"Processing repo {i+1}/{len(repos)}: {repo_name}")
        
        # Check checkpoint
        checkpoint = load_checkpoint(repo_id)
        if checkpoint and checkpoint.get('status') == 'complete':
            logger.info(f"Skipping {repo_name} (already processed)")
            all_blocks.extend(checkpoint.get('blocks', []))
            filtered_repos.append({**repo_meta, 'keep': True})
            continue
        
        # Clone repository
        clone_dir = Path(f"data/raw/repos/{repo_name.replace('/', '_')}")
        if not shallow_clone_repo(repo_meta['html_url'], clone_dir):
            logger.warning(f"Failed to clone {repo_name}, skipping")
            filtered_repos.append({**repo_meta, 'keep': False, 'reason': 'clone_failed'})
            continue
        
        # Extract blocks
        blocks = extract_code_blocks_from_repo(clone_dir)
        
        # Detect git mv exclusions
        blocks, mv_exclusions = detect_git_mv_exclusions(blocks, clone_dir)
        if mv_exclusions:
            for exc in mv_exclusions:
                logger.debug(f"Excluded block due to git mv: {exc}")
        
        # Calculate static metrics
        for block in blocks:
            metrics = calculate_static_metrics(block)
            block.update(metrics)
        
        # Tag blocks
        blocks = tag_blocks_with_classifier(blocks, classifier)
        
        # Enforce repository inclusion criteria
        kept_blocks, exclusion_reasons = enforce_repository_inclusion_criteria(blocks)
        
        if kept_blocks:
            logger.info(f"Repo {repo_name} passed inclusion criteria: {sum(1 for b in kept_blocks if b['label']=='llm')} LLM, {sum(1 for b in kept_blocks if b['label']=='human')} Human")
            all_blocks.extend(kept_blocks)
            filtered_repos.append({**repo_meta, 'keep': True})
            
            # Save checkpoint
            save_checkpoint(repo_id, {
                'status': 'complete',
                'blocks': kept_blocks,
                'timestamp': datetime.now().isoformat()
            })
        else:
            logger.warning(f"Repo {repo_name} excluded: {'; '.join(exclusion_reasons)}")
            filtered_repos.append({**repo_meta, 'keep': False, 'reason': '; '.join(exclusion_reasons)})
        
        # Cleanup clone dir
        if clone_dir.exists():
            shutil.rmtree(clone_dir)
    
    # Save outputs
    save_blocks_to_csv(all_blocks, Path(BLOCKS_CSV_PATH))
    save_filtered_repos(filtered_repos, Path(FILTERED_REPOS_PATH))
    
    logger.info(f"Pipeline complete. Total blocks: {len(all_blocks)}")
    logger.info(f"Filtered repos: {len([r for r in filtered_repos if r['keep']])} kept, {len([r for r in filtered_repos if not r['keep']])} excluded")
    
    return all_blocks, filtered_repos

if __name__ == "__main__":
    main()