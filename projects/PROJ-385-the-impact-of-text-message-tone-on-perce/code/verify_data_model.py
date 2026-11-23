"""
Data Model Validation Script (T004).

Validates specs/001-the-impact-of-text-message-tone-on-perce/data-model.md
against the required entities (Stimulus, Participant, Rating, AnalysisResult)
and checks for schema consistency.

Generates a validation report at data/validation/data_model_report.txt.
Raises an error if validation fails.
"""

import sys
import re
from pathlib import Path

# Import project utilities
from config import get_specs_dir, get_data_dir
from logging_config import setup_logging, get_logger

# Setup logger
logger = setup_logging()


def extract_entities_from_markdown(md_content: str) -> dict:
    """
    Extract entity definitions and schema tables from the markdown content.
    Returns a dict mapping entity names to their detected fields.
    """
    entities = {
        "Stimulus": [],
        "Participant": [],
        "Rating": [],
        "AnalysisResult": []
    }

    current_entity = None
    lines = md_content.splitlines()

    # Regex for entity headers (e.g., "### Stimulus")
    entity_header_pattern = re.compile(r'^###\s+(Stimulus|Participant|Rating|AnalysisResult)\s*$')
    # Regex for table rows (e.g., "| Field | Type | Description |")
    table_row_pattern = re.compile(r'^\|\s*(\w+)\s*\|\s*(\w+(?:\s*\([^)]*\))?)\s*\|')

    for line in lines:
        line = line.strip()
        if not line:
            continue

        header_match = entity_header_pattern.match(line)
        if header_match:
            current_entity = header_match.group(1)
            continue

        if current_entity and line.startswith("|"):
            # Skip header rows
            if "Field" in line and "Type" in line:
                continue
            # Skip separator rows
            if "---" in line:
                continue

            row_match = table_row_pattern.match(line)
            if row_match:
                field_name = row_match.group(1)
                field_type = row_match.group(2)
                entities[current_entity].append({
                    "field": field_name,
                    "type": field_type
                })

    return entities


def validate_entities(entities: dict) -> list:
    """
    Validate that the extracted entities match the expected schema requirements.
    Returns a list of error messages.
    """
    errors = []

    # Required fields per entity based on data-model.md and spec requirements
    required_fields = {
        "Stimulus": ["stimulus_id", "base_scenario", "emoji_count", "punctuation_pattern", "length_category", "cue_intensity", "full_text"],
        "Participant": ["participant_id"], # Minimal required for ID tracking
        "Rating": ["participant_id", "stimulus_id", "relationship_type", "rating", "timestamp"],
        "AnalysisResult": [] # AnalysisResult is an aggregate, usually defined by output schema
    }

    # Check Stimulus
    if "Stimulus" not in entities:
        errors.append("Missing 'Stimulus' entity definition.")
    else:
        found_fields = [f["field"] for f in entities["Stimulus"]]
        for req in required_fields["Stimulus"]:
            if req not in found_fields:
                errors.append(f"Stimulus entity missing required field: '{req}'")

    # Check Participant
    if "Participant" not in entities:
        errors.append("Missing 'Participant' entity definition.")
    else:
        found_fields = [f["field"] for f in entities["Participant"]]
        for req in required_fields["Participant"]:
            if req not in found_fields:
                errors.append(f"Participant entity missing required field: '{req}'")

    # Check Rating
    if "Rating" not in entities:
        errors.append("Missing 'Rating' entity definition.")
    else:
        found_fields = [f["field"] for f in entities["Rating"]]
        for req in required_fields["Rating"]:
            if req not in found_fields:
                errors.append(f"Rating entity missing required field: '{req}'")

    # Check AnalysisResult
    if "AnalysisResult" not in entities:
        # Note: AnalysisResult might be defined as a section rather than a table in some docs,
        # but the prompt asks to validate against the entities listed.
        # If it's missing entirely, it's a warning/error depending on strictness.
        # Given the prompt says "validate against spec.md entities", we expect it.
        errors.append("Missing 'AnalysisResult' entity definition.")

    return errors


def main():
    specs_dir = get_specs_dir()
    data_model_path = specs_dir / "001-the-impact-of-text-message-tone-on-perce" / "data-model.md"
    data_dir = get_data_dir()
    validation_dir = data_dir / "validation"

    # Ensure validation directory exists
    validation_dir.mkdir(parents=True, exist_ok=True)
    report_path = validation_dir / "data_model_report.txt"

    logger.info(f"Validating data model: {data_model_path}")

    if not data_model_path.exists():
        logger.error(f"Data model file not found: {data_model_path}")
        sys.exit(1)

    try:
        with open(data_model_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        logger.error(f"Failed to read data model: {e}")
        sys.exit(1)

    # Extract entities
    entities = extract_entities_from_markdown(content)

    # Validate
    errors = validate_entities(entities)

    # Generate Report
    report_lines = [
        "Data Model Validation Report",
        "=" * 40,
        f"Source: {data_model_path}",
        f"Status: {'PASSED' if not errors else 'FAILED'}",
        "",
        "Entities Detected:",
        "-" * 20
    ]

    for entity_name, fields in entities.items():
        report_lines.append(f"- {entity_name}: {len(fields)} fields found")
        if fields:
            for f in fields:
                report_lines.append(f"    - {f['field']} ({f['type']})")

    report_lines.append("")
    report_lines.append("Validation Checks:")
    report_lines.append("-" * 20)

    if errors:
        for err in errors:
            report_lines.append(f"[FAIL] {err}")
    else:
        report_lines.append("[PASS] All required entities and fields present.")

    # Write report
    report_content = "\n".join(report_lines)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    logger.info(f"Report written to: {report_path}")

    if errors:
        logger.error("Validation failed. Please review the report.")
        sys.exit(1)
    else:
        logger.info("Validation successful.")
        sys.exit(0)


if __name__ == "__main__":
    main()
