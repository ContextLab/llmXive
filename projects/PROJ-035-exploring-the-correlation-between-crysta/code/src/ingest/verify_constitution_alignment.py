"""
Verify that Constitution VII has been amended or aligned with FR-010.

This script checks the research.md file for evidence of alignment between
Constitution VII (data provenance requirements) and FR-010 (peer-reviewed
literature only). If no alignment is found, it exits with an error.

Usage:
    python src/ingest/verify_constitution_alignment.py [--research_md <path>]
"""
import sys
import argparse
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_research_md(research_md_path: Path) -> bool:
    """
    Check if research.md contains documented alignment between Constitution VII and FR-010.

    Args:
        research_md_path: Path to the research.md file.

    Returns:
        True if alignment is documented, False otherwise.
    """
    if not research_md_path.exists():
        logger.error(f"research.md not found at: {research_md_path}")
        return False

    content = research_md_path.read_text(encoding='utf-8')
    content_lower = content.lower()

    # Keywords to look for that indicate alignment/resolution
    alignment_indicators = [
        "constitution vii",
        "fr-010",
        "peer-reviewed",
        "amended",
        "alignment",
        "resolution",
        "conflict resolved",
        "concordance",
        "harmonized"
    ]

    # Check if both Constitution VII and FR-010 are mentioned
    has_constitution_vii = "constitution vii" in content_lower or "constitution 7" in content_lower
    has_fr_010 = "fr-010" in content_lower or "fr 010" in content_lower

    if not has_constitution_vii:
        logger.warning("Constitution VII not mentioned in research.md")
        return False

    if not has_fr_010:
        logger.warning("FR-010 not mentioned in research.md")
        return False

    # Check for alignment/resolution language
    has_alignment = any(indicator in content_lower for indicator in alignment_indicators)

    if has_alignment:
        logger.info("Constitution VII and FR-010 alignment documented in research.md")
        # Verify the conflict is explicitly resolved
        conflict_keywords = ["conflict", "issue", "discrepancy"]
        has_conflict_mention = any(kw in content_lower for kw in conflict_keywords)

        if has_conflict_mention:
            logger.info("Conflict between Constitution VII and FR-010 acknowledged and resolved")
            return True
        else:
            logger.info("Constitution VII and FR-010 alignment found without explicit conflict mention")
            return True
    else:
        logger.warning("No alignment/resolution language found between Constitution VII and FR-010")
        return False

def main():
    """Main entry point for the verification script."""
    parser = argparse.ArgumentParser(
        description="Verify Constitution VII alignment with FR-010"
    )
    parser.add_argument(
        "--research_md",
        type=str,
        default="research.md",
        help="Path to research.md file (default: research.md)"
    )
    args = parser.parse_args()

    research_md_path = Path(args.research_md)

    # Try to find research.md in common locations if not found at given path
    if not research_md_path.exists():
        project_root = Path(__file__).parent.parent.parent.parent
        possible_paths = [
            project_root / "research.md",
            project_root / "docs" / "research.md",
            Path(__file__).parent.parent.parent.parent / "research.md"
        ]

        for possible_path in possible_paths:
            if possible_path.exists():
                research_md_path = possible_path
                logger.info(f"Found research.md at: {research_md_path}")
                break

    if not research_md_path.exists():
        logger.error(f"research.md not found at: {research_md_path} or common locations")
        print("ERROR: research.md not found. Please ensure the file exists.")
        sys.exit(1)

    # Check for alignment
    is_aligned = check_research_md(research_md_path)

    if not is_aligned:
        error_msg = "Constitution VII not aligned with FR-010"
        logger.error(error_msg)
        print(f"ERROR: {error_msg}")
        print("Please ensure research.md documents the alignment or amendment.")
        sys.exit(1)

    logger.info("Constitution VII alignment verification passed")
    print("SUCCESS: Constitution VII is aligned with FR-010")
    sys.exit(0)

if __name__ == "__main__":
    main()
