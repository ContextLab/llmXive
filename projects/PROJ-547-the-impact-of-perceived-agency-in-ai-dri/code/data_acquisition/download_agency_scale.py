import hashlib
import urllib.request
from pathlib import Path
from logging.pipeline_logger import get_logger

logger = get_logger(__name__)


def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def download_file(url: str, dest_path: Path, expected_checksum: str | None = None) -> bool:
    """Download a file from a URL to a destination path."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Downloading {url} to {dest_path}")
    try:
        urllib.request.urlretrieve(url, dest_path)
        logger.info(f"Downloaded {url} successfully")
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        return False

    if expected_checksum:
        actual_checksum = compute_sha256(dest_path)
        if actual_checksum != expected_checksum:
            logger.error(
                f"Checksum mismatch for {dest_path}. "
                f"Expected: {expected_checksum}, Got: {actual_checksum}"
            )
            return False
        logger.info(f"Checksum verified for {dest_path}")

    return True


def main() -> None:
    """Main entry point for downloading the agency scale dataset."""
    # Hardcoded URL for the agency scale dataset
    url = "https://raw.githubusercontent.com/psych-data/agency-scale/main/data/agency_scale_sample.csv"
    dest_path = Path("data/external/agency_scale_sample.csv")
    expected_checksum = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    if download_file(url, dest_path, expected_checksum):
        logger.info("Agency scale dataset downloaded successfully")
    else:
        logger.error("Failed to download agency scale dataset")
        import sys
        sys.exit(1)


if __name__ == "__main__":
    main()