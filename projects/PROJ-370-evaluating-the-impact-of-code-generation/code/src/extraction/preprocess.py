import os
import json
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from code.config.settings import get_paths, get_config
from code.src.extraction.schema import BugDetection, Severity
from code.src.utils.logger import get_logger

logger = get_logger(__name__)

def estimate_tokens(text: str) -> int:
    """Estimate token count by splitting on whitespace and punctuation."""
    if not text:
        return 0
    # Simple heuristic: 1 word ≈ 1.3 tokens, or just count words for rough estimate
    words = text.split()
    return int(len(words) * 1.3)

def truncate_diff(diff_text: str, max_tokens: int = 8000) -> str:
    """Truncate diff if it exceeds context window."""
    if estimate_tokens(diff_text) <= max_tokens:
        return diff_text
    
    logger.warning(f"Diff exceeds {max_tokens} tokens, truncating.")
    # Truncate by removing middle content, keeping start and end
    lines = diff_text.splitlines()
    if len(lines) <= 10:
        return diff_text[:int(len(diff_text) * 0.5)]
    
    head_lines = 5
    tail_lines = 5
    truncated = "\n".join(lines[:head_lines]) + "\n...\n" + "\n".join(lines[-tail_lines:])
    return truncated

def preprocess_pr_data(pr_data: Dict[str, Any], max_tokens: int = 8000) -> Dict[str, Any]:
    """Preprocess a single PR's data, truncating large diffs."""
    processed = pr_data.copy()
    if "diff" in processed:
        processed["diff"] = truncate_diff(processed["diff"], max_tokens)
    return processed

def extract_raw_comments(pr_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract raw review comments from PR data."""
    comments = pr_data.get("review_comments", [])
    return [
        {
            "comment_id": c.get("id"),
            "author": c.get("user", {}).get("login"),
            "body": c.get("body"),
            "path": c.get("path"),
            "line": c.get("line"),
            "created_at": c.get("created_at")
        }
        for c in comments if c.get("body")
    ]

def generate_checksums(file_path: Path) -> str:
    """Generate SHA-256 checksum for a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def _is_likely_bug_comment(body: str) -> bool:
    """Heuristic to detect if a comment mentions a bug/issue."""
    keywords = ["bug", "issue", "fix", "error", "crash", "fail", "problem", "defect"]
    body_lower = body.lower()
    return any(kw in body_lower for kw in keywords)

def generate_human_baseline(prs_data: List[Dict[str, Any]], output_path: Path) -> List[Dict[str, Any]]:
    """
    Generate 'triangulated ground truth' in data/derived/human_baseline.json.
    
    Criteria (FR-011):
    (a) Requires linked issue AND ≥2 independent reviewers.
    (b) EXCLUDES any bug that does not meet strict criteria (NO fallback to "Closed Issue" alone).
    (c) Flags excluded bugs.
    
    Output Schema:
    List of objects with:
      - pr_id (str)
      - file_path (str)
      - line_start (int)
      - line_end (int)
      - severity (str: "critical", "major", "minor", "style")
      - is_verified (bool)
      - verification_method (str: "strict_triangulation" or "excluded_unverified")
    """
    baseline_entries = []
    
    for pr in prs_data:
        pr_id = pr.get("id") or pr.get("number")
        if not pr_id:
            continue
        
        # Extract linked issues
        linked_issues = pr.get("linked_issue_ids", [])
        has_linked_issue = len(linked_issues) > 0
        
        # Extract review comments
        comments = pr.get("review_comments", [])
        
        # Group comments by file/line to identify consensus
        # Structure: {(path, line): {author_set, comment_bodies}}
        bug_cues = {}
        
        for comment in comments:
            path = comment.get("path")
            line = comment.get("line")
            author = comment.get("author")
            body = comment.get("body", "")
            
            if not path or line is None or not author:
                continue
            
            # Heuristic: only consider comments that look like bug reports
            if not _is_likely_bug_comment(body):
                continue
            
            key = (path, line)
            if key not in bug_cues:
                bug_cues[key] = {"authors": set(), "bodies": []}
            
            bug_cues[key]["authors"].add(author)
            bug_cues[key]["bodies"].append(body)
        
        # Process each potential bug location
        for (file_path, line_start), cue_data in bug_cues.items():
            authors = cue_data["authors"]
            num_reviewers = len(authors)
            
            # Determine severity based on keyword intensity (simple heuristic)
            combined_body = " ".join(cue_data["bodies"]).lower()
            if any(kw in combined_body for kw in ["crash", "fatal", "security", "data loss"]):
                severity = "critical"
            elif any(kw in combined_body for kw in ["error", "fail", "broken"]):
                severity = "major"
            elif any(kw in combined_body for kw in ["minor", "style", "typo"]):
                severity = "style"
            else:
                severity = "minor"
            
            # Apply Triangulation Criteria
            is_verified = False
            verification_method = "excluded_unverified"
            
            # Strict criteria: Linked Issue AND >= 2 independent reviewers
            if has_linked_issue and num_reviewers >= 2:
                is_verified = True
                verification_method = "strict_triangulation"
            
            entry = {
                "pr_id": str(pr_id),
                "file_path": file_path,
                "line_start": line_start,
                "line_end": line_start, # Assuming single line for now, could be extended
                "severity": severity,
                "is_verified": is_verified,
                "verification_method": verification_method
            }
            
            baseline_entries.append(entry)
            
            if not is_verified:
                reason = f"PR {pr_id}: Bug at {file_path}:{line_start} excluded. "
                if not has_linked_issue:
                    reason += "Missing linked issue. "
                if num_reviewers < 2:
                    reason += f"Only {num_reviewers} reviewer(s) found. "
                logger.warning(reason)

    # Write to output file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(baseline_entries, f, indent=2)
    
    logger.info(f"Generated human baseline with {len(baseline_entries)} entries at {output_path}")
    return baseline_entries

def main():
    """Main entry point to generate human baseline from raw PR data."""
    paths = get_paths()
    raw_dir = paths["raw"]
    derived_dir = paths["derived"]
    
    raw_files = list(Path(raw_dir).glob("pr_*.json"))
    
    if not raw_files:
        logger.error(f"No raw PR data found in {raw_dir}. Run fetch_prs first.")
        return

    all_pr_data = []
    for f in raw_files:
        with open(f, "r", encoding="utf-8") as fp:
            data = json.load(fp)
            # Handle single PR or list of PRs
            if isinstance(data, list):
                all_pr_data.extend(data)
            else:
                all_pr_data.append(data)
    
    logger.info(f"Loaded {len(all_pr_data)} PRs for baseline generation.")
    
    output_path = Path(derived_dir) / "human_baseline.json"
    generate_human_baseline(all_pr_data, output_path)

if __name__ == "__main__":
    main()
