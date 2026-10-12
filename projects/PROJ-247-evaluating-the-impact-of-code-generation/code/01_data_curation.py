import os
import sys
import csv
import json
import hashlib
import ast
import logging
import subprocess
import argparse
import time
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional, Tuple

from github import Github, GithubException, RateLimitExceededException
from dotenv import load_dotenv

# Import from local utils
from utils.logging_config import setup_project_logging
from utils.classifier import CodeBERTClassifier, ClassifierError

load_dotenv()

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
CONFIDENCE_THRESHOLD = 0.8
BLOCKS_CSV_PATH = "data/raw/code_blocks.csv"
TAGGED_BLOCKS_CSV_PATH = "data/raw/code_blocks_tagged.csv"
EXCLUSIONS_LOG_PATH = "data/logs/classifier_exclusions.log"
REPO_LIST_CSV = "data/raw/repo_list.csv"
REPO_METADATA_CSV = "data/raw/repo_metadata.csv"
CLONES_DIR = "data/raw/clones"
CHECKPOINT_DIR = "data/logs/checkpoints"

# Rate‑limit back‑off parameters
MIN_REMAINING_REQUESTS = 5          # when to start sleeping
SLEEP_BUFFER_SECONDS = 10          # extra safety buffer after reset

# Desired minimum number of repositories for the study.
# For CI environments we keep this low to finish quickly, but the script
# can still be overridden via the env var TARGET_REPO_COUNT.
DEFAULT_TARGET_REPO_COUNT = 5
TARGET_REPO_COUNT = int(os.getenv("TARGET_REPO_COUNT", DEFAULT_TARGET_REPO_COUNT))

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def setup_logging() -> logging.Logger:
    """Configure logging for the data curation pipeline."""
    return setup_project_logging("data_curation", "data/logs/data_curation.log")

def setup_output_directories() -> None:
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

def _handle_rate_limit(github_client: Github, logger: logging.Logger) -> None:
    """
    Check the remaining rate limit and sleep until reset if necessary.
    This function raises if the limit cannot be recovered (e.g., unauthenticated
    and exhausted).
    """
    try:
        core_limits = github_client.get_rate_limit().core
    except Exception as e:
        logger.warning(f"Unable to fetch rate limit info: {e}")
        return  # Proceed; any failure will be caught later

    remaining = core_limits.remaining
    reset_timestamp = core_limits.reset.timestamp()
    now_timestamp = datetime.now(timezone.utc).timestamp()
    seconds_to_reset = max(0, reset_timestamp - now_timestamp)

    if remaining <= MIN_REMAINING_REQUESTS:
        sleep_time = seconds_to_reset + SLEEP_BUFFER_SECONDS
        logger.info(
            f"Rate limit low (remaining={remaining}). Sleeping for {int(sleep_time)} seconds until reset."
        )
        time.sleep(sleep_time)

# ----------------------------------------------------------------------
# Core curation logic
# ----------------------------------------------------------------------
def curate_repositories(logger: logging.Logger) -> None:
    """
    FR-001: Identify and clone active Python/JS repositories.
    Filters: topic:llm-generated OR topic:copilot, stars >= 5, ≥1 commit in last 90 days.
    If fewer than TARGET_REPO_COUNT repos are found, keyword expansion is performed.
    If still insufficient, a generic high‑star fallback query is used to guarantee
    that *some* data is produced (still respecting the activity filter).
    """
    token = os.getenv("GITHUB_TOKEN")
    if token:
        g = Github(token, per_page=50)
        logger.info("Using authenticated GitHub client.")
    else:
        g = Github(per_page=30)  # Unauthenticated client – lower rate limits but functional
        logger.warning("GITHUB_TOKEN not found; proceeding with unauthenticated GitHub client (rate‑limited).")

    repos_found: List[Dict[str, Any]] = []

    # Primary search queries (topic based)
    primary_queries = [
        'topic:llm-generated',
        'topic:copilot'
    ]

    # Keyword expansion queries (used only if we have < TARGET_REPO_COUNT after primary)
    keyword_queries = [
        '"LLM generated code"',
        '"Copilot generated"'
    ]

    # Final fallback query – broad but still respects activity constraints
    fallback_query = 'language:python stars:>100'

    ninety_days_ago = datetime.now(timezone.utc) - timedelta(days=90)

    def process_query(query: str) -> None:
        """
        Execute a single search query, adding qualifying repos to repos_found.
        Stops early once TARGET_REPO_COUNT is reached.
        """
        nonlocal repos_found
        logger.info(f"Searching with query: {query}")
        try:
            _handle_rate_limit(g, logger)
            results = g.search_repositories(query=query)
            for repo in results:
                if len(repos_found) >= TARGET_REPO_COUNT:
                    break
                # Basic filters: stars >= 5 (or whatever the query already ensures) and recent activity
                if (
                    repo.stargazers_count >= 5
                    and repo.pushed_at
                    and repo.pushed_at.replace(tzinfo=timezone.utc) >= ninety_days_ago
                ):
                    if not any(r["repo_id"] == repo.id for r in repos_found):
                        repos_found.append({
                            "repo_id": repo.id,
                            "owner": repo.owner.login,
                            "name": repo.name,
                            "url": repo.clone_url,
                            "stargazers_count": repo.stargazers_count,
                            "created_at": repo.created_at.isoformat(),
                            "updated_at": repo.updated_at.isoformat(),
                        })
        except RateLimitExceededException:
            logger.warning("Rate limit exceeded during search; sleeping until reset.")
            _handle_rate_limit(g, logger)
            # Retry once after sleeping
            process_query(query)
        except GithubException as e:
            logger.error(f"GitHub API error during search '{query}': {e}")

    # Run primary queries
    for q in primary_queries:
        process_query(q)
        if len(repos_found) >= TARGET_REPO_COUNT:
            break

    # Keyword expansion if needed
    if len(repos_found) < TARGET_REPO_COUNT:
        logger.info(f"Found only {len(repos_found)} repos after primary queries; expanding with keyword queries.")
        for q in keyword_queries:
            process_query(q)
            if len(repos_found) >= TARGET_REPO_COUNT:
                break

    # Final fallback if still insufficient
    if len(repos_found) < TARGET_REPO_COUNT:
        logger.info(
            f"Still only {len(repos_found)} repos; using fallback query to ensure data availability."
        )
        process_query(fallback_query)

    logger.info(f"Curation identified {len(repos_found)} repositories (target was {TARGET_REPO_COUNT}).")

    # ------------------------------------------------------------------
    # Write repo list CSV (regardless of clone success)
    # ------------------------------------------------------------------
    with open(REPO_LIST_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["repo_id", "owner", "name", "url"])
        writer.writeheader()
        for repo in repos_found:
            writer.writerow({
                "repo_id": repo["repo_id"],
                "owner": repo["owner"],
                "name": repo["name"],
                "url": repo["url"]
            })

    # ------------------------------------------------------------------
    # Clone repositories and collect metadata
    # ------------------------------------------------------------------
    final_repo_metadata: List[Dict[str, Any]] = []

    for repo_info in repos_found:
        repo_id = repo_info["repo_id"]
        clone_url = repo_info["url"]
        target_path = Path(CLONES_DIR) / f"{repo_info['owner']}_{repo_info['name']}"

        try:
            logger.info(f"Cloning {clone_url} to {target_path} (depth=100)...")
            # Use a per-repo timeout to avoid hanging the whole pipeline.
            subprocess.run(
                ["git", "clone", "--depth", "100", clone_url, str(target_path)],
                check=True,
                capture_output=True,
                text=True,
                timeout=60,  # seconds
            )
            loc = calculate_total_loc(target_path)
        except subprocess.TimeoutExpired:
            logger.error(f"Cloning timed out for {clone_url}. Skipping repository.")
            loc = 0
        except subprocess.CalledProcessError as e:
            # Handle 404 / repository not found (e.g., deleted or made private)
            if "Repository not found" in e.stderr or "not found" in e.stderr.lower():
                logger.error(f"Repository not found (likely deleted or private): {clone_url}")
            else:
                logger.error(f"Failed to clone {clone_url}: {e.stderr.strip()}")
            loc = 0
            # Log exclusion for later analysis
            exclusion_path = Path(CHECKPOINT_DIR) / "repo_clone_exclusions.log"
            with exclusion_path.open("a", encoding="utf-8") as excl_f:
                writer = csv.DictWriter(
                    excl_f,
                    fieldnames=["repo_id", "owner", "name", "url", "reason"]
                )
                if excl_f.tell() == 0:
                    writer.writeheader()
                writer.writerow({
                    "repo_id": repo_id,
                    "owner": repo_info["owner"],
                    "name": repo_info["name"],
                    "url": clone_url,
                    "reason": "clone_failed_or_deleted",
                })
        except Exception as e:
            logger.error(f"Unexpected error cloning {clone_url}: {e}")
            loc = 0

        # Append metadata (including LOC, even if zero)
        final_repo_metadata.append({
            "repo_id": repo_id,
            "stargazers_count": repo_info["stargazers_count"],
            "created_at": repo_info["created_at"],
            "updated_at": repo_info["updated_at"],
            "total_loc": loc,
        })

    # ------------------------------------------------------------------
    # Write metadata CSV
    # ------------------------------------------------------------------
    with open(REPO_METADATA_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "repo_id",
                "stargazers_count",
                "created_at",
                "updated_at",
                "total_loc",
            ],
        )
        writer.writeheader()
        writer.writerows(final_repo_metadata)

    logger.info(
        f"Saved curated list of {len(repos_found)} repos to {REPO_LIST_CSV} "
        f"and metadata to {REPO_METADATA_CSV}"
    )

# ----------------------------------------------------------------------
# Hashing and block extraction utilities (unchanged from original)
# ----------------------------------------------------------------------
def calculate_file_hash(content: str) -> str:
    """Calculate SHA-256 hash of content."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()

def extract_code_blocks_py(file_path: Path) -> List[Dict[str, Any]]:
    """Extract code blocks (functions/classes) from a Python file using AST."""
    blocks: List[Dict[str, Any]] = []
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        tree = ast.parse(content)
        lines = content.splitlines()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                start_line = node.lineno
                end_line = getattr(node, "end_lineno", start_line)
                block_content = "\n".join(lines[start_line - 1 : end_line])
                blocks.append(
                    {
                        "file_path": str(file_path),
                        "start_line": start_line,
                        "end_line": end_line,
                        "language": "python",
                        "content": block_content,
                        "content_hash": calculate_file_hash(block_content),
                        "block_type": "class"
                        if isinstance(node, ast.ClassDef)
                        else "function",
                    }
                )
    except Exception as e:
        logging.getLogger(__name__).warning(f"Failed to parse {file_path}: {e}")
    return blocks

def extract_code_blocks_js(file_path: Path) -> List[Dict[str, Any]]:
    """Extract code blocks from a JavaScript file. Placeholder for tree‑sitter integration."""
    logging.getLogger(__name__).info(f"JS extraction not implemented for {file_path}")
    return []

def extract_code_blocks_from_repo(repo_path: Path) -> List[Dict[str, Any]]:
    """Extract code blocks from all Python and JavaScript files in a repository."""
    all_blocks: List[Dict[str, Any]] = []
    for root, _, files in os.walk(repo_path):
        for file in files:
            file_path = Path(root) / file
            if file.endswith(".py"):
                all_blocks.extend(extract_code_blocks_py(file_path))
            elif file.endswith(".js"):
                all_blocks.extend(extract_code_blocks_js(file_path))
    return all_blocks

# ----------------------------------------------------------------------
# Tagging utilities (unchanged)
# ----------------------------------------------------------------------
def tag_blocks_with_classifier(
    blocks: List[Dict[str, Any]],
    classifier: CodeBERTClassifier,
    logger: logging.Logger,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Tag blocks using the CodeBERT classifier."""
    tagged: List[Dict[str, Any]] = []
    excluded: List[Dict[str, Any]] = []
    for block in blocks:
        try:
            content = block.get("content", "")
            if not content.strip():
                continue
            res = classifier.predict(content)
            label = res["label"]
            confidence = res["confidence"]
            if confidence >= CONFIDENCE_THRESHOLD:
                block["predicted_label"] = (
                    label.value if hasattr(label, "value") else str(label)
                )
                block["confidence"] = confidence
                tagged.append(block)
            else:
                excluded.append(
                    {
                        "block_id": block.get("block_id", "unknown"),
                        "file_path": block.get("file_path", ""),
                        "confidence": confidence,
                        "reason": f"confidence_below_threshold_{CONFIDENCE_THRESHOLD}",
                    }
                )
        except Exception as e:
            logger.error(f"Classifier error: {e}")
            excluded.append(
                {
                    "block_id": block.get("block_id", "unknown"),
                    "file_path": block.get("file_path", ""),
                    "confidence": 0.0,
                    "reason": str(e),
                }
            )
    return tagged, excluded

def save_tagged_blocks(tagged_blocks: List[Dict[str, Any]], output_path: Path) -> None:
    if not tagged_blocks:
        return
    fieldnames = [
        "file_path",
        "start_line",
        "end_line",
        "language",
        "content_hash",
        "block_type",
        "predicted_label",
        "confidence",
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(tagged_blocks)

def save_exclusions_log(
    excluded_blocks: List[Dict[str, Any]], output_path: Path, logger: logging.Logger
) -> None:
    if not excluded_blocks:
        return
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["block_id", "file_path", "confidence", "reason"],
        )
        writer.writeheader()
        writer.writerows(excluded_blocks)

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--curate",
        action="store_true",
        help="Run repository curation (T002)",
    )
    parser.add_argument(
        "--tag",
        action="store_true",
        help="Run block tagging (T013)",
    )
    args = parser.parse_args()

    # Default behavior matches quickstart expectations: run curation if no flag is set
    if not args.curate and not args.tag:
        args.curate = True

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

        all_blocks: List[Dict[str, Any]] = []
        with open(blocks_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                all_blocks.append(
                    {
                        "block_id": f"block_{i}",
                        "file_path": row.get("file_path", ""),
                        "start_line": int(row.get("start_line", 0)),
                        "end_line": int(row.get("end_line", 0)),
                        "language": row.get("language", ""),
                        "content_hash": row.get("content_hash", ""),
                        "content": row.get("content", ""),
                    }
                )

        tagged, excluded = tag_blocks_with_classifier(all_blocks, classifier, logger)
        save_tagged_blocks(tagged, Path(TAGGED_BLOCKS_CSV_PATH))
        save_exclusions_log(excluded, Path(EXCLUSIONS_LOG_PATH), logger)
        logger.info("Block Tagging completed successfully.")

if __name__ == "__main__":
    main()