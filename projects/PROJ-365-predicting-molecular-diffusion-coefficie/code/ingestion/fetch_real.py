import sys
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from utils.config import get_project_root
from utils.logging import get_logger, log_info, log_error

logger = get_logger(__name__)

def ensure_output_dir(output_path: Path) -> None:
    """Ensure the directory for the output file exists."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

def fetch_from_zenodo(url: str, output_path: Path) -> None:
    """
    Download a file from a Zenodo URL.
    Zenodo often provides a 'latest' redirect or a direct file link.
    We handle the redirect by using urlopen which follows redirects automatically.
    """
    log_info(logger, f"Attempting to download from Zenodo: {url}")
    try:
        req = Request(url, headers={'User-Agent': 'llmXive-pipeline'})
        with urlopen(req, timeout=30) as response:
            ensure_output_dir(output_path)
            with open(output_path, 'wb') as f:
                while True:
                    chunk = response.read(8192)
                    if not chunk:
                        break
                    f.write(chunk)
        log_info(logger, f"Successfully downloaded to {output_path}")
    except (URLError, HTTPError) as e:
        log_error(logger, f"Failed to download from Zenodo: {e}")
        raise FileNotFoundError(f"Could not download dataset from Zenodo: {e}")

def fetch_from_nist(url: str, output_path: Path) -> None:
    """
    Download a file from a NIST URL.
    NIST data might require specific headers or follow different redirection rules.
    """
    log_info(logger, f"Attempting to download from NIST: {url}")
    try:
        req = Request(url, headers={'User-Agent': 'llmXive-pipeline'})
        with urlopen(req, timeout=30) as response:
            ensure_output_dir(output_path)
            with open(output_path, 'wb') as f:
                while True:
                    chunk = response.read(8192)
                    if not chunk:
                        break
                    f.write(chunk)
        log_info(logger, f"Successfully downloaded to {output_path}")
    except (URLError, HTTPError) as e:
        log_error(logger, f"Failed to download from NIST: {e}")
        raise FileNotFoundError(f"Could not download dataset from NIST: {e}")

def update_plan_md(plan_path: Path, dataset_url: str) -> None:
    """
    Update plan.md to record the actual dataset URL if it's not already present.
    """
    if not plan_path.exists():
        log_error(logger, f"Plan file not found: {plan_path}")
        return

    content = plan_path.read_text()
    # Check if Dataset URL: line already exists
    if "Dataset URL:" in content:
        log_info(logger, "Dataset URL already present in plan.md, skipping update.")
        return

    # Append the URL to the plan
    with open(plan_path, 'a', encoding='utf-8') as f:
        f.write(f"\nDataset URL: {dataset_url}\n")
    log_info(logger, f"Updated plan.md with Dataset URL: {dataset_url}")

def main():
    root = get_project_root()
    plan_path = root / "plan.md"
    raw_dir = root / "data" / "raw"
    output_file = raw_dir / "dataset.csv"

    # Ensure raw directory exists
    raw_dir.mkdir(parents=True, exist_ok=True)

    # 1. Check plan.md for Dataset URL
    if not plan_path.exists():
        log_error(logger, "plan.md not found. Cannot fetch real data.")
        print("ERROR: plan.md not found.")
        sys.exit(1)

    plan_content = plan_path.read_text()
    dataset_url = None
    for line in plan_content.splitlines():
        if line.strip().startswith("Dataset URL:"):
            dataset_url = line.split(":", 1)[1].strip()
            break

    if not dataset_url:
        log_info(logger, "No 'Dataset URL:' found in plan.md. Triggering synthetic generation (T048).")
        print("NO_URL")
        sys.exit(0)

    log_info(logger, f"Found Dataset URL in plan.md: {dataset_url}")

    # 2. Attempt download
    try:
        # Determine fetch strategy based on URL (simple heuristic)
        if "zenodo" in dataset_url.lower():
            fetch_from_zenodo(dataset_url, output_file)
        elif "nist" in dataset_url.lower() or "nist.gov" in dataset_url.lower():
            fetch_from_nist(dataset_url, output_file)
        else:
            # Generic fetch attempt
            log_info(logger, f"Attempting generic fetch from: {dataset_url}")
            req = Request(dataset_url, headers={'User-Agent': 'llmXive-pipeline'})
            with urlopen(req, timeout=30) as response:
                ensure_output_dir(output_file)
                with open(output_file, 'wb') as f:
                    while True:
                        chunk = response.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)
            log_info(logger, f"Successfully downloaded to {output_file}")

        # 3. Update plan.md if successful (redundant check but safe)
        update_plan_md(plan_path, dataset_url)
        print("SUCCESS")
        sys.exit(0)

    except FileNotFoundError as e:
        log_error(logger, str(e))
        print("FAILED")
        sys.exit(1)
    except Exception as e:
        log_error(logger, f"Unexpected error during download: {e}")
        print("FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()
