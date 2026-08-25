"""
Task T011a: Map JSVulnDB Schema to BigVul-Like Schema.

This script generates the mapping definition required to transform JSVulnDB
raw fields into the standard ground-truth schema (CodeSnippet) used by the pipeline.

It outputs a JSON file `data/logs/jsvulndb_mapping.json` containing the field
mapping rules and a sample transformation logic description.

The mapping is designed to align JSVulnDB's specific JSON structure with the
BigVul-like schema (code, label, language, cwe_id, file_name, line_number).
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

# Import project utilities
from src.utils.logger import get_logger, log_stage_start, log_stage_complete, log_stage_failure
from src.utils.config import get_project_root

logger = get_logger(__name__)

# JSVulnDB Source Field Assumptions (based on standard JSVulnDB JSON structure)
# Source: https://github.com/BigVul/JSVulnDB or similar repository structure
# Typical fields in JSVulnDB JSON entries:
# - "id": unique identifier
# - "filename": path to the file
# - "line": line number of the vulnerability
# - "code": the actual code snippet
# - "cwe": CWE ID (e.g., "CWE-79")
# - "type": vulnerability type (e.g., "XSS", "SQLi")
# - "description": text description

# Target Schema (BigVul-like / CodeSnippet):
# - code (str)
# - ground_truth_label (int: 1 for vulnerable, 0 for safe)
# - language (str: "javascript")
# - cwe_category (str: e.g., "CWE-79")
# - file_name (str)
# - line_number (int)

JSVULNDB_TO_BIGVUL_MAPPING: Dict[str, Any] = {
    "description": "Mapping from JSVulnDB raw JSON fields to the unified CodeSnippet schema.",
    "source_dataset": "JSVulnDB",
    "target_schema": "CodeSnippet (BigVul-like)",
    "field_mappings": {
        "code": {
            "source_field": "code",
            "transformation": "Direct copy. Ensure no None values.",
            "target_type": "str"
        },
        "ground_truth_label": {
            "source_field": "None (Implicit)",
            "transformation": "Constant value 1 (JSVulnDB is a vulnerability dataset, all entries are vulnerable).",
            "target_type": "int",
            "default_value": 1
        },
        "language": {
            "source_field": "None (Implicit)",
            "transformation": "Constant value 'javascript'.",
            "target_type": "str",
            "default_value": "javascript"
        },
        "cwe_category": {
            "source_field": "cwe",
            "transformation": "Extract numeric ID if prefixed with 'CWE-' (e.g., 'CWE-79' -> 'CWE-79'). Normalize to uppercase.",
            "target_type": "str"
        },
        "file_name": {
            "source_field": "filename",
            "transformation": "Direct copy.",
            "target_type": "str"
        },
        "line_number": {
            "source_field": "line",
            "transformation": "Convert to integer. Handle potential string inputs.",
            "target_type": "int"
        }
    },
    "validation_rules": [
        "All 'code' fields must be non-empty strings.",
        "All 'cwe' fields must match the pattern 'CWE-\\d+'.",
        "All 'line' fields must be positive integers."
    ],
    "example_transformation": {
        "input": {
            "id": "12345",
            "filename": "example.js",
            "line": "42",
            "code": "eval(userInput);",
            "cwe": "CWE-94",
            "type": "Code Injection"
        },
        "output": {
            "code": "eval(userInput);",
            "ground_truth_label": 1,
            "language": "javascript",
            "cwe_category": "CWE-94",
            "file_name": "example.js",
            "line_number": 42
        }
    }
}

def generate_mapping_document() -> Dict[str, Any]:
    """
    Generates the complete mapping document including metadata and rules.
    """
    logger.info("Generating JSVulnDB to BigVul mapping document.")
    return JSVULNDB_TO_BIGVUL_MAPPING

def write_mapping_json(mapping_doc: Dict[str, Any], output_path: Path) -> None:
    """
    Writes the mapping document to the specified JSON path.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(mapping_doc, f, indent=2, ensure_ascii=False)
    logger.info(f"Mapping document written to {output_path}")

def main():
    """
    Main entry point for Task T011a.
    """
    log_stage_start(logger, "T011a", "Map JSVulnDB Schema to BigVul-Like Schema")
    
    try:
        project_root = get_project_root()
        output_path = project_root / "data" / "logs" / "jsvulndb_mapping.json"
        
        # Generate the mapping document
        mapping_doc = generate_mapping_document()
        
        # Write to disk
        write_mapping_json(mapping_doc, output_path)
        
        log_stage_complete(logger, "T011a", f"Mapping saved to {output_path}")
        return 0
        
    except Exception as e:
        log_stage_failure(logger, "T011a", str(e))
        return 1

if __name__ == "__main__":
    exit(main())
