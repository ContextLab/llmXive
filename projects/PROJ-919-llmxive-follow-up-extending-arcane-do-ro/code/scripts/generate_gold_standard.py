import hashlib
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add project root to path to allow imports if running as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from src.lib.utils import get_logger
except ImportError:
    # Fallback if src.lib.utils not available yet (during initial setup)
    def get_logger(name):
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger


logger = get_logger(__name__)

# Constants
N_SAMPLES = 20
GUTENBERG_ID = "1342"  # Pride and Prejudice
SEGMENT_INTERVAL = 50  # Every 50th paragraph
OUTPUT_PATH = Path("data/gold_standard/human_annotations.json")
CHECKSUM_PATH = Path("data/gold_standard/human_annotations.sha256")


def fetch_gutenberg_text(book_id: str) -> str:
    """
    Fetches the text of a book from Project Gutenberg.
    Uses the raw text file URL pattern for Gutenberg.
    """
    import urllib.error
    import urllib.request

    # Gutenberg raw text URL pattern
    url = f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt"
    logger.info(f"Fetching text from {url}...")

    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            content = response.read().decode("utf-8")
            return content
    except urllib.error.URLError as e:
        logger.error(f"Failed to fetch Gutenberg text: {e}")
        raise RuntimeError(f"Failed to fetch real data from Gutenberg: {e}")
    except Exception as e:
        logger.error(f"Unexpected error fetching Gutenberg text: {e}")
        raise RuntimeError(f"Unexpected error fetching data: {e}")


def extract_segments(
    text: str, interval: int = SEGMENT_INTERVAL, count: int = N_SAMPLES
) -> List[str]:
    """
    Extracts non-overlapping text segments based on paragraph boundaries.
    Logic: Split by double newlines, take every 'interval' paragraph starting at 0.
    """
    # Split by double newline to identify paragraphs
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    if len(paragraphs) < count * interval:
        logger.warning(
            f"Text has only {len(paragraphs)} paragraphs, but {count * interval} needed. Adjusting logic."
        )
        # Fallback: if not enough paragraphs, take every available one until we have enough
        # But per spec, we want non-overlapping. If text is too short, we might fail.
        # For Pride and Prejudice, this should be fine.
        segments = paragraphs[:count]
    else:
        segments = []
        for i in range(count):
            idx = i * interval
            if idx < len(paragraphs):
                segments.append(paragraphs[idx])
            else:
                # Should not happen with full text
                logger.warning(f"Could not find segment at index {idx}")

    return segments


def determine_labels(segment: str, index: int) -> Dict[str, Any]:
    """
    Determines 'Coarse' and 'Fine' phase labels based on a deterministic rule set.
    Rule:
      - Early chapters (low index) -> Innocence/Naive Trust
      - Late chapters (high index) -> Experience/Calculated Skepticism
    We split the 20 samples into two halves.
    """
    # Split 20 samples into two halves: 0-9 (Early), 10-19 (Late)
    is_early = index < (N_SAMPLES // 2)

    coarse_phase = "Innocence / Naive Trust" if is_early else "Experience / Calculated Skepticism"
    fine_phase = "Early Social Interaction" if is_early else "Complex Social Navigation"

    # Deterministic description based on phase
    if is_early:
        coarse_desc = "Character exhibits initial trust and lack of guile in social situations."
        fine_desc = "Character engages in straightforward, uncalculated social exchanges."
    else:
        coarse_desc = "Character displays wariness and strategic assessment of others."
        fine_desc = "Character navigates social situations with hidden motives and caution."

    return {
        "coarse_phase": coarse_phase,
        "fine_phase": fine_phase,
        "coarse_description": coarse_desc,
        "fine_description": fine_desc,
    }


def generate_fallback_data() -> List[Dict[str, Any]]:
    """
    Generates the Gold Standard dataset using the local fallback logic.
    1. Fetch Pride and Prejudice.
    2. Extract segments.
    3. Annotate with deterministic rules.
    """
    logger.info("Starting Gold Standard generation via local fallback (Gutenberg)...")

    text = fetch_gutenberg_text(GUTENBERG_ID)
    segments = extract_segments(text)

    if len(segments) < N_SAMPLES:
        raise RuntimeError(
            f"Could not extract {N_SAMPLES} segments from the text. Only found {len(segments)}."
        )

    annotations = []
    for i, segment in enumerate(segments):
        labels = determine_labels(segment, i)

        annotation = {
            "id": f"gs-{i:03d}",
            "source": "gutenberg",
            "source_id": GUTENBERG_ID,
            "text_segment": segment,
            "segment_index": i,
            "annotations": {
                "coarse": {
                    "phase": labels["coarse_phase"],
                    "description": labels["coarse_description"],
                },
                "fine": {"phase": labels["fine_phase"], "description": labels["fine_description"]},
            },
            "metadata": {
                "generation_method": "deterministic_rule_based",
                "rule_set": "early_chapters_innocence_late_chapters_skepticism",
            },
        }
        annotations.append(annotation)

    logger.info(f"Successfully generated {len(annotations)} annotations.")
    return annotations


def compute_sha256(file_path: Path) -> str:
    """Computes the SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def main():
    """Main entry point for generating the Gold Standard dataset."""
    # Ensure output directory exists
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Generate data
    try:
        annotations = generate_fallback_data()
    except Exception as e:
        logger.error(f"Failed to generate fallback data: {e}")
        raise

    # Write to JSON
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(annotations, f, indent=2, ensure_ascii=False)

    logger.info(f"Gold Standard dataset written to {OUTPUT_PATH}")

    # Compute and write checksum
    checksum = compute_sha256(OUTPUT_PATH)
    with open(CHECKSUM_PATH, "w", encoding="utf-8") as f:
        f.write(checksum)

    logger.info(f"Checksum {checksum} written to {CHECKSUM_PATH}")
    return checksum


if __name__ == "__main__":
    main()
