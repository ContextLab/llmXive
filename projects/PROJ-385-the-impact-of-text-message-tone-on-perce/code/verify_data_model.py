"""Verification script for the data model markdown.

This script checks that the `data-model.md` file located in the specs
directory defines the four required entities:

- Stimulus
- Participant
- Rating
- AnalysisResult

It writes a short validation report to ``data/validation_report.txt`` and
exits with a non‑zero status code if any required entity is missing.
"""

import sys
from pathlib import Path

from config import get_specs_dir, get_data_dir
from logging_config import setup_logging, get_logger


EXPECTED_ENTITIES = {"Stimulus", "Participant", "Rating", "AnalysisResult"}


def extract_entities_from_markdown(md_path: Path) -> set:
    """Extract top‑level entity headings (### Entity) from a markdown file."""
    entities: set = set()
    with md_path.open(encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped.startswith("### "):
                # Heading format: ### EntityName
                name = stripped[4:].strip()
                # Only keep the first word in case extra description is present
                name = name.split()[0]
                entities.add(name)
    return entities


def validate_entities(found: set) -> tuple[set, set]:
    """Return ``(missing, unexpected)`` sets compared to the expected list."""
    missing = EXPECTED_ENTITIES - found
    unexpected = found - EXPECTED_ENTITIES
    return missing, unexpected


def main() -> None:
    """Run the validation and write a short report."""
    # Initialise logging – the logger writes to the console; the report is
    # written to a file in the data directory.
    setup_logging()
    logger = get_logger(__name__)

    md_path = (
        get_specs_dir()
        / "001-the-impact-of-text-message-tone-on-perce"
        / "data-model.md"
    )
    if not md_path.is_file():
        logger.error(f"Data model markdown not found at {md_path}")
        sys.exit(1)

    logger.info(f"Reading data model from {md_path}")
    found_entities = extract_entities_from_markdown(md_path)
    missing, unexpected = validate_entities(found_entities)

    # Ensure the data directory exists before writing the report.
    report_path = get_data_dir() / "validation_report.txt"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with report_path.open("w", encoding="utf-8") as report:
        if missing:
            report.write(f"Missing entities: {', '.join(sorted(missing))}\\n")
        if unexpected:
            report.write(
                f"Unexpected entities: {', '.join(sorted(unexpected))}\\n"
            )
        if not missing and not unexpected:
            report.write("All expected entities are present.\\n")

    if missing:
        logger.error(f"Missing required entities: {', '.join(sorted(missing))}")
        sys.exit(2)
    if unexpected:
        logger.warning(
            f"Found unexpected entities (ignored): {', '.join(sorted(unexpected))}"
        )

    logger.info("Data model validation passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
