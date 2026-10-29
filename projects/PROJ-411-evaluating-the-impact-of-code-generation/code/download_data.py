"""
download_data.py

Phase 0 script: download raw pull-request metadata from the GitHub REST API.
The script reads a list of repositories (owner/repo) from a text file,
fetches pull requests, enriches each PR with the required fields defined in 
`raw_prs.schema.yaml`, validates the presence of those fields, and writes 
one JSON file per repository under `data/raw/`. It also creates a combined 
JSON file for downstream processing, a SHA-256 checksums file, and a 
markdown schema-mapping report.

To avoid timeouts on massive repositories and respect unauthenticated 
rate limits (60 requests/hour), the script defaults to fetching a 
small number of PRs. This can be increased via --max-prs if a 
GITHUB_TOKEN is provided.
"""
import argparse
import hashlib
import json
import os
import random
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

import pandas as pd
import requests
import yaml

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
GITHUB_API = "https://api.github.com"
MAX_RETRIES = 5
BACKOFF_BASE = 2 
PER_PAGE = 100    
# Default reduced to 10 to ensure CI completion without a token (approx 30-40 calls/repo)
DEFAULT_MAX_PRS = 10  

SCHEMA_PATH = (
    paths.root
    / "specs"
    / "001-evaluating-the-impact-of-code-generation"
    / "contracts"
    / "raw_prs.schema.yaml"
)

# ----------------------------------------------------------------------
# Helper functions (schema handling)
# ----------------------------------------------------------------------
def _normalize_name(name: str) -> str:
    return name.lower().replace("_", "")

def load_schema_required_fields(schema_path: Path) -> List[str]:
    if not schema_path.is_file():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)
    required = schema.get("required", [])
    if not isinstance(required, list):
        raise RuntimeError("Invalid schema: 'required' must be a list")
    return required

def load_schema_all_fields(schema_path: Path) -> List[str]:
    if not schema_path.is_file():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)
    properties = schema.get("properties", {})
    if not isinstance(properties, dict):
        raise RuntimeError("Invalid schema: 'properties' must be a dict")
    return list(properties.keys())

def compute_sha256(file_path: Path) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def write_checksums(checksum_dict: Dict[Path, str], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for p, chksum in checksum_dict.items():
            f.write(f"{p.name}\t{chksum}\n")

def write_schema_map(map_info: Dict[str, Dict[str, str]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("# Schema Mapping Report\n\n")
        for tag, info in map_info.items():
            f.write(f"## Dataset: {tag}\n\n")
            f.write("| Variable | Status |\n")
            f.write("|---|---|\n")
            for var, status in info.items():
                f.write(f"| `{var}` | {status} |\n")
            f.write("\n")

def validate_columns(df: pd.DataFrame, fields: List[str]) -> Dict[str, str]:
    existing_norm = {_normalize_name(col): col for col in df.columns}
    status: Dict[str, str] = {}
    for field in fields:
        norm_field = _normalize_name(field)
        status[field] = "present" if norm_field in existing_norm else "missing"
    return status

# ----------------------------------------------------------------------
# HTTP utilities
# ----------------------------------------------------------------------
def _request(url: str, params: Dict = None) -> requests.Response:
    attempt = 0
    headers = {}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"
    while True:
        attempt += 1
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=30)
        except requests.RequestException as exc:
            raise RuntimeError(f"Network error while contacting {url}: {exc}")

        remaining = int(resp.headers.get("X-RateLimit-Remaining", "0"))
        reset_ts = int(resp.headers.get("X-RateLimit-Reset", "0"))
        if remaining == 0:
            sleep_seconds = max(reset_ts - int(time.time()), 0) + 1
            log.warning(f"Rate limit exhausted. Sleeping for {sleep_seconds}s until reset.")
            time.sleep(sleep_seconds)
            continue 

        if resp.status_code in (429, 403):
            if attempt >= MAX_RETRIES:
                raise RuntimeError(f"Exceeded max retries ({MAX_RETRIES}) for URL {url}: status {resp.status_code}")
            backoff = BACKOFF_BASE ** attempt + random.random()
            log.warning(f"Received {resp.status_code} from {url}. Back-off {backoff:.2f}s (attempt {attempt}).")
            time.sleep(backoff)
            continue

        if not resp.ok:
            raise RuntimeError(f"Failed request to {url}: HTTP {resp.status_code} – {resp.text}")
        return resp

# ----------------------------------------------------------------------
# Data extraction helpers
# ----------------------------------------------------------------------
def _fetch_pulls(owner: str, repo: str, max_prs: int) -> List[Dict]:
    pulls = []
    page = 1
    while len(pulls) < max_prs:
        url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls"
        params = {"state": "all", "per_page": PER_PAGE, "page": page}
        resp = _request(url, params=params)
        batch = resp.json()
        if not isinstance(batch, list) or not batch:
            break
        pulls.extend(batch)
        if len(batch) < PER_PAGE:
            break
        page += 1
    return pulls[:max_prs]

def _fetch_pr_detail(owner: str, repo: str, number: int) -> Dict:
    url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{number}"
    return _request(url).json()

def _fetch_commit_message(owner: str, repo: str, sha: str) -> str:
    url = f"{GITHUB_API}/repos/{owner}/{repo}/commits/{sha}"
    data = _request(url).json()
    return data.get("commit", {}).get("message", "")

def _fetch_first_comment_timestamp(owner: str, repo: str, number: int) -> Optional[str]:
    url = f"{GITHUB_API}/repos/{owner}/{repo}/issues/{number}/comments"
    comments = _request(url, params={"per_page": PER_PAGE}).json()
    if not comments or not isinstance(comments, list):
        return None
    earliest = min(comments, key=lambda c: c.get("created_at", ""))
    return earliest.get("created_at")

# ----------------------------------------------------------------------
# Main workflow
# ----------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-list", type=str, required=True)
    parser.add_argument("--output", type=str, required=False)
    parser.add_argument("--max-prs", type=int, default=DEFAULT_MAX_PRS)
    args = parser.parse_args()

    repo_list_path = Path(args.repo_list)
    if not repo_list_path.is_file():
        raise FileNotFoundError(f"Repository list file not found: {repo_list_path}")

    output_dir = Path(args.output) if args.output else paths.data("raw")
    output_dir.mkdir(parents=True, exist_ok=True)

    required_fields = load_schema_required_fields(SCHEMA_PATH)
    all_fields = load_schema_all_fields(SCHEMA_PATH)
    log.info(f"Schema required fields: {required_fields}")

    checksum_dict: Dict[Path, str] = {}
    schema_map: Dict[str, Dict[str, str]] = {}
    all_enriched_records = []

    with open(repo_list_path, "r", encoding="utf-8") as f:
        repo_lines = [ln.strip() for ln in f.readlines() if ln.strip()]

    for line in repo_lines:
        if "/" not in line:
            continue
        owner, repo = line.split("/", 1)
        log.info(f"Processing {owner}/{repo}...")

        raw_prs = _fetch_pulls(owner, repo, args.max_prs)
        enriched_records = []

        for pr in raw_prs:
            number = pr.get("number")
            if number is None: continue

            detail = _fetch_pr_detail(owner, repo, number)
            head_sha = detail.get("head", {}).get("sha")
            commit_msg = _fetch_commit_message(owner, repo, head_sha) if head_sha else ""
            
            comment_cnt = pr.get("comments", 0) or 0
            first_comment_ts = _fetch_first_comment_timestamp(owner, repo, number) if comment_cnt > 0 else None

            record = {
                "pr_id": number,
                "repo_name": f"{owner}/{repo}",
                "created_at": pr.get("created_at"),
                "merged_at": pr.get("merged_at"),
                "additions": detail.get("additions", 0),
                "deletions": detail.get("deletions", 0),
                "comment_count": comment_cnt,
                "commit_message": commit_msg,
                "first_comment_timestamp": first_comment_ts,
                "diff_text": None,
                "file_headers": None,
                "labels": pr.get("labels", []),
            }
            
            # Abort loudly if any required field is missing from the record keys
            for field in required_fields:
                if field not in record:
                    raise RuntimeError(f"Required field '{field}' missing from PR {number} in {owner}/{repo}")
            
            enriched_records.append(record)
            all_enriched_records.append(record)

        json_path = output_dir / f"{owner}_{repo}_prs.json"
        with open(json_path, "w", encoding="utf-8") as jf:
            json.dump(enriched_records, jf, ensure_ascii=False, indent=2)

        checksum_dict[json_path] = compute_sha256(json_path)
        df_repo = pd.DataFrame(enriched_records)
        schema_map[json_path.name] = validate_columns(df_repo, all_fields)

    # Also write a combined file as expected by classify_provenance.py in quickstart.md
    combined_path = output_dir / "combined_prs.json"
    with open(combined_path, "w", encoding="utf-8") as cf:
        json.dump(all_enriched_records, cf, ensure_ascii=False, indent=2)
    checksum_dict[combined_path] = compute_sha256(combined_path)

    write_checksums(checksum_dict, paths.data("checksums.txt"))
    write_schema_map(schema_map, output_dir / "schema_map.md")

    quickstart_path = paths.root / "specs" / "001-evaluating-the-impact-of-code-generation" / "quickstart.md"
    cmd = f"python code/download_data.py --repo-list {args.repo_list} --output {args.output or 'data/raw/'}"
    try:
        with open(quickstart_path, "a", encoding="utf-8") as f:
            f.write(f"\n```bash\n# Recorded command for reproducibility\n{cmd}\n```\n")
    except Exception as e:
        log.warning(f"Could not update quickstart: {e}")

    log.info("Download completed successfully.")

if __name__ == "__main__":
    main()