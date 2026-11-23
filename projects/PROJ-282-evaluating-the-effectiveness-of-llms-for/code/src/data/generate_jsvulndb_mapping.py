import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

from src.utils.logger import get_logger, log_stage_start, log_stage_complete, log_stage_failure

# The target schema (BigVul-like) expected for the unified dataset.
# Based on T007b (CodeSnippet) and standard vulnerability datasets:
# - snippet_id: Unique identifier (string)
# - language: Programming language (string, e.g., "JavaScript")
# - code: The source code snippet (string)
# - ground_truth_label: Binary label (0 = safe, 1 = vulnerable)
# - cwe_id: Common Weakness Enumeration ID (string or int)
# - vulnerability_type: Human-readable category name (string)
# - source_file: Original file path (string)
# - line_number: Line number in original file (int)
# - description: Optional description of the vulnerability (string)

JSVULNDB_TO_BIGVUL_MAPPING = {
    "jsvulndb_id": "snippet_id",
    "language": "language",
    "code": "code",
    "vulnerable": "ground_truth_label",
    "cwe": "cwe_id",
    "category": "vulnerability_type",
    "file": "source_file",
    "line": "line_number",
    "description": "description"
}

# Specific mapping notes for JSVulnDB quirks
MAPPING_NOTES = {
    "vulnerable": "JSVulnDB uses boolean or 0/1. Target is integer 0 or 1.",
    "cwe": "JSVulnDB may store CWE as 'CWE-123' or just '123'. Target should be standardized string 'CWE-XXX' or int.",
    "category": "JSVulnDB categories must be normalized to match BigVul's taxonomy (e.g., 'SQL Injection', 'XSS').",
    "line": "JSVulnDB line numbers might be 0-indexed or 1-indexed. Target is 1-indexed."
}

def generate_mapping_document() -> Dict[str, Any]:
    """
    Generates a comprehensive mapping document describing how JSVulnDB fields
    map to the project's unified ground-truth schema (BigVul-like).
    """
    return {
        "source_dataset": "JSVulnDB",
        "target_schema": "BigVul-Like (Unified CodeSnippet)",
        "field_mappings": JSVULNDB_TO_BIGVUL_MAPPING,
        "transformation_rules": {
            "ground_truth_label": {
                "source_type": "boolean/int",
                "target_type": "int",
                "logic": "Convert True/1 to 1, False/0 to 0."
            },
            "cwe_id": {
                "source_type": "string/int",
                "target_type": "string",
                "logic": "Ensure format 'CWE-XXXX'. If raw int, prepend 'CWE-'."
            },
            "vulnerability_type": {
                "source_type": "string",
                "target_type": "string",
                "logic": "Map JSVulnDB categories to standard BigVul categories."
            }
        },
        "notes": MAPPING_NOTES
    }

def write_mapping_json(mapping_doc: Dict[str, Any], output_path: Path) -> None:
    """
    Writes the mapping document to a JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(mapping_doc, f, indent=2)

def main() -> int:
    """
    Main entry point for T011a: Map JSVulnDB Schema to BigVul-Like Schema.
    """
    logger = get_logger("T011a_mapping")
    log_stage_start(logger, "Mapping JSVulnDB schema to BigVul-like schema")

    try:
        # Determine output path based on project config
        # Assuming standard project structure: data/logs/
        project_root = Path(__file__).resolve().parents[3]
        logs_dir = project_root / "data" / "logs"
        output_file = logs_dir / "jsvulndb_mapping.json"

        mapping_doc = generate_mapping_document()
        write_mapping_json(mapping_doc, output_file)

        log_stage_complete(
            logger,
            "Mapping document generated successfully",
            artifact_path=str(output_file)
        )
        return 0

    except Exception as e:
        log_stage_failure(logger, f"Failed to generate mapping: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main())
