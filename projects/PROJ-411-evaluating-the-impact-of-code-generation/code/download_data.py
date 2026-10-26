"""
download_data.py

Phase 0 script: download raw pull‑request metadata from the GitHub REST API.
The script reads a list of repositories (owner/repo) from a text file,
fetches *all* pull requests (including closed and merged ones), enriches each
PR with the required fields defined in ``raw_prs.schema.yaml``, validates the
presence of those fields, and writes one JSON file per repository under
``data/raw/``.  It also creates a SHA‑256 checksums file and a markdown
schema‑mapping report.

Rate‑limit handling:
  * After each request the ``X-RateLimit-Remaining`` header is inspected.
  * If the remaining quota is 0, the script sleeps until the
    ``X-RateLimit-Reset`` epoch time.
  * For HTTP 429 or 403 responses an exponential back‑off (max 5 attempts)
    with jitter is applied.

The implementation purposefully avoids any synthetic data – all values are
fetched from the live GitHub API (unauthenticated requests are sufficient for
the tiny demo repository list used in the CI).
"""
import argparse
import hashlib
import json
import time
import random
from pathlib import Path
from typing import Dict, List

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
BACKOFF_BASE = 2  # exponential factor
PER_PAGE = 100    # GitHub pagination size

# Schema location (project‑relative)
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
    """Normalise a column or field name for fuzzy matching."""
    return name.lower().replace("_", "")

def load_schema_required_fields(schema_path: Path) -> List[str]:
    """Load the JSON‑schema file and return the list of *required* property names."""
    if not schema_path.is_file():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)
    required = schema.get("required", [])
    if not isinstance(required, list):
        raise RuntimeError("Invalid schema: 'required' must be a list")
    return required

def load_schema_all_fields(schema_path: Path) -> List[str]:
    """Return a list of **all** property keys defined in the schema."""
    if not schema_path.is_file():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)
    properties = schema.get("properties", {})
    if not isinstance(properties, dict):
        raise RuntimeError("Invalid schema: 'properties' must be a dict")
    return list(properties.keys())

def compute_sha256(file_path: Path) -> str:
    """Compute SHA‑256 checksum of a file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def write_checksums(checksum_dict: Dict[Path, str], out_path: Path) -> None:
    """Write SHA‑256 checksums to a text file."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for p, chksum in checksum_dict.items():
            f.write(f"{p.name}\t{chksum}\n")

def write_schema_map(map_info: Dict[str, Dict[str, str]], out_path: Path) -> None:
    """Write a markdown table documenting variable availability per dataset."""
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
    """
    For each field in ``fields`` report whether it is present in ``df``.
    Returns a mapping ``field -> status`` where status is either
    ``present`` or ``missing``.
    """
    existing_norm = {_normalize_name(col): col for col in df.columns}
    status: Dict[str, str] = {}
    for field in fields:
        norm_field = _normalize_name(field)
        status[field] = "present" if norm_field in existing_norm else "missing"
    return status

# ----------------------------------------------------------------------
# HTTP utilities with rate‑limit & back‑off handling
# ----------------------------------------------------------------------
def _request(url: str, params: Dict = None) -> requests.Response:
    """GET request with exponential back‑off for 429/403 responses."""
    attempt = 0
    while True:
        attempt += 1
        try:
            resp = requests.get(url, params=params, timeout=30)
        except requests.RequestException as exc:
            raise RuntimeError(f"Network error while contacting {url}: {exc}")

        # Rate‑limit handling (unauthenticated: 60 req/hr)
        remaining = int(resp.headers.get("X-RateLimit-Remaining", "0"))
        reset_ts = int(resp.headers.get("X-RateLimit-Reset", "0"))
        if remaining == 0:
            sleep_seconds = max(reset_ts - int(time.time()), 0) + 1
            log.warning(
                f"Rate limit exhausted. Sleeping for {sleep_seconds}s until reset."
            )
            time.sleep(sleep_seconds)
            continue  # retry after sleep

        if resp.status_code in (429, 403):
            if attempt >= MAX_RETRIES:
                raise RuntimeError(
                    f"Exceeded max retries ({MAX_RETRIES}) for URL {url}: "
                    f"status {resp.status_code}"
                )
            backoff = BACKOFF_BASE ** attempt + random.random()
            log.warning(
                f"Received {resp.status_code} from {url}. Back‑off {backoff:.2f}s (attempt {attempt})."
            )
            time.sleep(backoff)
            continue

        if not resp.ok:
            raise RuntimeError(
                f"Failed request to {url}: HTTP {resp.status_code} – {resp.text}"
            )
        return resp

# ----------------------------------------------------------------------
# Data extraction helpers
# ----------------------------------------------------------------------
def _fetch_all_pulls(owner: str, repo: str) -> List[Dict]:
    """Retrieve all pull requests (any state) for a repository."""
    pulls = []
    page = 1
    while True:
        url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls"
        params = {"state": "all", "per_page": PER_PAGE, "page": page}
        resp = _request(url, params=params)
        batch = resp.json()
        if not isinstance(batch, list):
            raise RuntimeError(f"Unexpected PR list payload for {owner}/{repo}")
        pulls.extend(batch)
        if len(batch) < PER_PAGE:
            break
        page += 1
    log.info(f"Fetched {len(pulls)} PRs for {owner}/{repo}")
    return pulls

def _fetch_pr_detail(owner: str, repo: str, number: int) -> Dict:
    """Fetch detailed PR information (adds additions/deletions)."""
    url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{number}"
    resp = _request(url)
    return resp.json()

def _fetch_commit_message(owner: str, repo: str, sha: str) -> str:
    """Retrieve the commit message for a given SHA."""
    url = f"{GITHUB_API}/repos/{owner}/{repo}/commits/{sha}"
    resp = _request(url)
    data = resp.json()
    # The nested structure follows the GitHub API spec.
    return data.get("commit", {}).get("message", "")

def _fetch_first_comment_timestamp(owner: str, repo: str, number: int) -> str:
    """
    Return ISO‑8601 timestamp of the earliest *issue* comment on the PR.
    If no comments exist, return ``None`` (the schema allows null).
    """
    url = f"{GITHUB_API}/repos/{owner}/{repo}/issues/{number}/comments"
    resp = _request(url, params={"per_page": PER_PAGE})
    comments = resp.json()
    if not comments:
        return None
    # comments are already ordered newest‑first; find earliest.
    earliest = min(comments, key=lambda c: c.get("created_at", ""))
    return earliest.get("created_at")

# ----------------------------------------------------------------------
# Main workflow
# ----------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download raw PR data from GitHub and validate against the schema."
    )
    parser.add_argument(
        "--repo-list",
        type=str,
        required=True,
        help="Path to a text file listing target repositories (owner/repo).",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=False,
        help="Output directory (defaults to data/raw/).",
    )
    args = parser.parse_args()

    repo_list_path = Path(args.repo_list)
    if not repo_list_path.is_file():
        raise FileNotFoundError(f"Repository list file not found: {repo_list_path}")

    output_dir = Path(args.output) if args.output else paths.data("raw")
    output_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Load schema information
    # ------------------------------------------------------------------
    required_fields = load_schema_required_fields(SCHEMA_PATH)
    all_fields = load_schema_all_fields(SCHEMA_PATH)
    log.info(f"Schema required fields: {required_fields}")

    # ------------------------------------------------------------------
    # Process each repository
    # ------------------------------------------------------------------
    checksum_dict: Dict[Path, str] = {}
    schema_map: Dict[str, Dict[str, str]] = {}

    with open(repo_list_path, "r", encoding="utf-8") as f:
        repo_lines = [ln.strip() for ln in f.readlines() if ln.strip()]

    for line in repo_lines:
        if "/" not in line:
            log.warning(f"Ignoring malformed repository entry: '{line}'")
            continue
        owner, repo = line.split("/", 1)

        # 1️⃣ Fetch basic PR list
        raw_prs = _fetch_all_pulls(owner, repo)

        enriched_records = []
        for pr in raw_prs:
            number = pr.get("number")
            if number is None:
                continue

            # 2️⃣ Fetch detailed PR (additions/deletions)
            detail = _fetch_pr_detail(owner, repo, number)

            # 3️⃣ Resolve commit message (head SHA)
            head_sha = detail.get("head", {}).get("sha")
            commit_msg = _fetch_commit_message(owner, repo, head_sha) if head_sha else ""

            # 4️⃣ First comment timestamp (may be None)
            first_comment_ts = _fetch_first_comment_timestamp(owner, repo, number)

            record = {
                "pr_id": number,
                "repo_name": f"{owner}/{repo}",
                "created_at": pr.get("created_at"),
                "merged_at": pr.get("merged_at"),
                "additions": detail.get("additions", 0),
                "deletions": detail.get("deletions", 0),
                "comment_count": pr.get("comments", 0),
                "commit_message": commit_msg,
                "first_comment_timestamp": first_comment_ts,
                # Optional fields left as null (schema permits)
                "diff_text": None,
                "file_headers": None,
                "labels": pr.get("labels", []),
            }
            enriched_records.append(record)

        # Write JSON file for this repository
        json_path = output_dir / f"{owner}_{repo}_prs.json"
        with open(json_path, "w", encoding="utf-8") as jf:
            json.dump(enriched_records, jf, ensure_ascii=False, indent=2)

        log.info(f"Wrote {len(enriched_records)} records to {json_path}")

        # Compute checksum
        checksum_dict[json_path] = compute_sha256(json_path)

        # Schema‑map for this file
        df_repo = pd.DataFrame(enriched_records)
        schema_map[json_path.name] = validate_columns(df_repo, all_fields)

    # ------------------------------------------------------------------
    # Write checksums file
    # ------------------------------------------------------------------
    checksums_path = paths.data("checksums.txt")
    write_checksums(checksum_dict, checksums_path)
    log.info(f"Checksums written to {checksums_path}")

    # ------------------------------------------------------------------
    # Write schema‑mapping markdown report
    # ------------------------------------------------------------------
    schema_map_path = output_dir / "schema_map.md"
    write_schema_map(schema_map, schema_map_path)
    log.info(f"Schema mapping report written to {schema_map_path}")

    # ------------------------------------------------------------------
    # Record the exact command line in quickstart.md (reproducibility)
    # ------------------------------------------------------------------
    quickstart_path = (
        paths.root
        / "specs"
        / "001-evaluating-the-impact-of-code-generation"
        / "quickstart.md"
    )
    command_line = (
        "python code/download_data.py "
        "--repo-list code/repo_list.txt "
        "--output data/raw/"
    )
    try:
        with open(quickstart_path, "a", encoding="utf-8") as f:
            f.write("\n```bash\n# Recorded command for reproducibility\n")
            f.write(f"{command_line}\n```\n")
        log.info(f"Command logged in {quickstart_path}")
    except Exception as exc:
        log.warning(f"Failed to log command in quickstart.md: {exc}")

    log.info("Download and validation completed successfully.")

if __name__ == "__main__":
    main()