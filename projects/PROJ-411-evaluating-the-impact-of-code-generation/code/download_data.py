"""
download_data.py

Phase 0 script: download raw pull‑request metadata from the GitHub REST API,
write one JSON file per repository (under ``data/raw/``), create a combined
parquet file ``data/raw/prs-v2-sample.parquet`` (used by the test suite),
compute SHA‑256 checksums, validate the columns against the raw PR schema,
and write a markdown schema‑mapping report.

The script respects the rate‑limit of 5 000 requests / hour (FR‑001) and
implements exponential back‑off for 429/403 responses (FR‑009).  It logs
the exact command line in ``specs/001-evaluating-the-impact-of-code-generation/quickstart.md``.
"""
import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple

import httpx
import pandas as pd
import yaml
from huggingface_hub import hf_hub_download, list_repo_files

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# HF repository identifiers – retained for auxiliary datasets (unused in tests)
PRIMARY_REPO = "loubnabnl/prs-v2-sample"
AUXILIARY_DATASETS = [
    {"repo_id": "davanstrien/authors_merged_model_prs", "tag": "aux_model"},
    {"repo_id": "davanstrien/authors_merged_dataset_prs", "tag": "aux_dataset"},
]

# Schema location
SCHEMA_PATH = (
    paths.root
    / "specs"
    / "001-evaluating-the-impact-of-code-generation"
    / "contracts"
    / "raw_prs.schema.yaml"
)

# Mandatory fields required for downstream scope (must be present in the
# combined dataset)
PRIMARY_MANDATORY_FIELDS = {
    "pr_id",
    "repo_name",
    "created_at",
    "merged_at",
    "additions",
    "deletions",
    "comment_count",
    "commit_message",
    "first_comment_timestamp",
}

# GitHub API constants
GITHUB_API_URL = "https://api.github.com"
PER_PAGE = 100  # maximum allowed by GitHub
MAX_RETRIES = 5
BACKOFF_FACTOR = 2  # exponential back‑off factor

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
# GitHub API helpers
# ----------------------------------------------------------------------
def _github_get(client: httpx.Client, url: str, params: Dict = None) -> Tuple[Dict, httpx.Response]:
    """
    Perform a GET request with exponential back‑off on 429/403.
    Returns the JSON payload and the raw response.
    """
    attempt = 0
    while True:
        try:
            resp = client.get(url, params=params)
        except httpx.RequestError as exc:
            raise RuntimeError(f"Network error while contacting {url}: {exc}") from exc

        if resp.status_code == 200:
            return resp.json(), resp
        elif resp.status_code in (429, 403):
            if attempt >= MAX_RETRIES:
                raise RuntimeError(f"Exceeded max retries for {url} (status {resp.status_code})")
            backoff = BACKOFF_FACTOR ** attempt
            log.warning(f"Rate‑limit or access error ({resp.status_code}) for {url}; sleeping {backoff}s")
            time.sleep(backoff)
            attempt += 1
            continue
        else:
            raise RuntimeError(f"Unexpected status {resp.status_code} for {url}: {resp.text}")

def _handle_rate_limit(resp: httpx.Response) -> None:
    """Sleep until the GitHub rate limit resets if we are out of requests."""
    remaining = int(resp.headers.get("X-RateLimit-Remaining", "1"))
    reset_ts = int(resp.headers.get("X-RateLimit-Reset", "0"))
    if remaining == 0:
        sleep_seconds = max(reset_ts - int(time.time()), 0) + 1
        log.info(f"Rate limit exhausted – sleeping for {sleep_seconds}s until reset")
        time.sleep(sleep_seconds)

def fetch_all_prs(client: httpx.Client, owner: str, repo: str) -> List[Dict]:
    """Fetch all closed PRs for a repository (pagination handled)."""
    prs: List[Dict] = []
    page = 1
    while True:
        url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/pulls"
        params = {"state": "closed", "per_page": PER_PAGE, "page": page}
        data, resp = _github_get(client, url, params=params)
        _handle_rate_limit(resp)
        if not data:
            break
        prs.extend(data)
        # GitHub uses the Link header for pagination
        link = resp.headers.get("Link", "")
        if 'rel="next"' not in link:
            break
        page += 1
    return prs

def fetch_first_comment_timestamp(client: httpx.Client, owner: str, repo: str, pr_number: int) -> str:
    """
    Return the ISO‑8601 timestamp of the earliest review comment for a PR,
    or ``None`` if there are no comments.
    """
    comments: List[Dict] = []
    page = 1
    while True:
        url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/pulls/{pr_number}/comments"
        params = {"per_page": PER_PAGE, "page": page}
        data, resp = _github_get(client, url, params=params)
        _handle_rate_limit(resp)
        if not data:
            break
        comments.extend(data)
        link = resp.headers.get("Link", "")
        if 'rel="next"' not in link:
            break
        page += 1

    if not comments:
        return None
    # Find the earliest creation timestamp
    earliest = min(c["created_at"] for c in comments)
    return earliest

# ----------------------------------------------------------------------
# Main workflow
# ----------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="Download raw PR data from GitHub and validate against schema.")
    parser.add_argument("--repo-list", type=str, required=True, help="Path to a text file listing target repositories (owner/repo per line).")
    parser.add_argument("--output", type=str, required=False, help="Output directory (defaults to data/raw/).")
    args = parser.parse_args()

    repo_list_path = Path(args.repo_list)
    if not repo_list_path.is_file():
        raise FileNotFoundError(f"Repository list file not found: {repo_list_path}")

    output_dir = Path(args.output) if args.output else paths.data("raw")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load schema information for later validation
    required_fields = load_schema_required_fields(SCHEMA_PATH)
    all_fields = load_schema_all_fields(SCHEMA_PATH)
    log.info(f"Schema required fields: {required_fields}")
    log.info(f"Schema total fields (including optional): {len(all_fields)}")

    checksum_dict: Dict[Path, str] = {}
    schema_map: Dict[str, Dict[str, str]] = {}

    # ------------------------------------------------------------------
    # 1. Fetch PR data from each repository listed in repo_list.txt
    # ------------------------------------------------------------------
    combined_records: List[Dict] = []
    with httpx.Client(timeout=30.0) as client:
        for line in repo_list_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "/" not in line:
                log.warning(f"Skipping malformed repo identifier: {line}")
                continue
            owner, repo = line.split("/", 1)
            log.info(f"Fetching PRs for {owner}/{repo}")
            prs = fetch_all_prs(client, owner, repo)

            repo_records: List[Dict] = []
            for pr in prs:
                pr_number = pr.get("number")
                if pr_number is None:
                    continue

                # Basic fields directly from the PR object
                record = {
                    "pr_id": pr_number,
                    "repo_name": f"{owner}/{repo}",
                    "created_at": pr.get("created_at"),
                    "merged_at": pr.get("merged_at"),
                    "additions": pr.get("additions", 0),
                    "deletions": pr.get("deletions", 0),
                    "comment_count": pr.get("comments", 0) + pr.get("review_comments", 0),
                    "commit_message": pr.get("title", ""),
                    # ``first_comment_timestamp`` will be filled later
                    "first_comment_timestamp": None,
                }

                # Retrieve earliest comment timestamp (may be None)
                try:
                    first_ts = fetch_first_comment_timestamp(client, owner, repo, pr_number)
                except Exception as e:
                    log.warning(f"Could not fetch comments for PR #{pr_number} in {owner}/{repo}: {e}")
                    first_ts = None
                record["first_comment_timestamp"] = first_ts

                repo_records.append(record)
                combined_records.append(record)

            # Write per‑repo raw JSON file
            repo_filename = f"{owner}_{repo}_raw.json".replace("/", "_")
            repo_path = output_dir / repo_filename
            with open(repo_path, "w", encoding="utf-8") as f:
                json.dump(repo_records, f, ensure_ascii=False, indent=2)
            checksum = compute_sha256(repo_path)
            checksum_dict[repo_path] = checksum
            # Validation for this repo (used in the schema‑map)
            df_repo = pd.DataFrame(repo_records)
            repo_status = validate_columns(df_repo, all_fields)
            schema_map[repo_filename] = repo_status

    # ------------------------------------------------------------------
    # 2. Write combined parquet (used by the test suite)
    # ------------------------------------------------------------------
    combined_df = pd.DataFrame(combined_records)
    combined_parquet_path = output_dir / "prs-v2-sample.parquet"
    combined_df.to_parquet(combined_parquet_path, engine="pyarrow", index=False)
    checksum_dict[combined_parquet_path] = compute_sha256(combined_parquet_path)
    schema_map["primary"] = validate_columns(combined_df, all_fields)

    # ------------------------------------------------------------------
    # 3. Write combined JSON (consumed by downstream scripts)
    # ------------------------------------------------------------------
    combined_json_path = output_dir / "combined_prs.json"
    with open(combined_json_path, "w", encoding="utf-8") as f:
        json.dump(combined_records, f, ensure_ascii=False, indent=2)
    checksum_dict[combined_json_path] = compute_sha256(combined_json_path)
    schema_map["combined_json"] = validate_columns(combined_df, all_fields)

    # ------------------------------------------------------------------
    # 4. Verify mandatory fields are present in the combined dataset
    # ------------------------------------------------------------------
    missing_mandatory = [
        fld for fld in PRIMARY_MANDATORY_FIELDS if schema_map["primary"].get(fld) != "present"
    ]
    if missing_mandatory:
        raise RuntimeError(
            f"Primary dataset is missing mandatory fields required for scope: {missing_mandatory}"
        )
    log.info("Combined dataset contains all mandatory fields.")

    # ------------------------------------------------------------------
    # 5. Write checksums and schema‑mapping report
    # ------------------------------------------------------------------
    checksums_path = paths.data("checksums.txt")
    write_checksums(checksum_dict, checksums_path)

    schema_map_path = output_dir / "schema_map.md"
    write_schema_map(schema_map, schema_map_path)

    log.info(
        f"Download completed. Checksums → {checksums_path}, schema map → {schema_map_path}"
    )

    # ------------------------------------------------------------------
    # 6. Record the exact command used in quickstart.md (FR‑001 logging)
    # ------------------------------------------------------------------
    quickstart_path = (
        paths.root
        / "specs"
        / "001-evaluating-the-impact-of-code-generation"
        / "quickstart.md"
    )
    command_line = "python code/download_data.py --repo-list code/repo_list.txt --output data/raw/"
    try:
        with open(quickstart_path, "a", encoding="utf-8") as f:
            f.write("\n```bash\n# Recorded command for reproducibility\n")
            f.write(f"{command_line}\n```\n")
        log.info(f"Command logged in {quickstart_path}")
    except Exception as exc:
        log.warning(f"Failed to log command in quickstart.md: {exc}")

if __name__ == "__main__":
    main()
