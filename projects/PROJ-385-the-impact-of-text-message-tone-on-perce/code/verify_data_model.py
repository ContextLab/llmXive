"""
verify_data_model.py

Validates the existing specs/001-the-impact-of-text-message-tone-on-perce/data-model.md
against the current spec requirements for Stimulus, Participant, Rating, and AnalysisResult entities.

This script:
1. Checks if the data-model.md file exists.
2. Parses the markdown to extract the defined entities and their schemas.
3. Validates the content against a reference schema (defined in this script).
4. Prints a report and exits with 0 if valid, 1 if invalid.
"""

import sys
import re
from pathlib import Path

# Reference schema definition based on the task description and spec.md requirements
REFERENCE_SCHEMA = {
    "Stimulus": [
        "stimulus_id",
        "base_scenario",
        "emoji_count",
        "punctuation_pattern",
        "length_category",
        "cue_intensity",
        "full_text"
    ],
    "Participant": [
        "participant_id",
        "relationship_type", # Often linked in Rating, but entity context requires ID
        "rating"             # Contextual, but Participant entity must exist
    ],
    "Rating": [
        "participant_id",
        "stimulus_id",
        "relationship_type",
        "rating",
        "timestamp"
    ],
    "AnalysisResult": [
        "term",
        "estimate",
        "std_error",
        "df",
        "t_value",
        "p_value",
        "ci_lower",
        "ci_upper"
    ]
}

def extract_entities_from_markdown(md_content: str) -> dict:
    """
    Extracts entity definitions and their fields from the markdown content.
    Looks for sections like "## 1. Stimulus Schema" or "### Stimulus".
    """
    found_entities = {}
    
    # Pattern to find table headers or entity definitions
    # We look for lines starting with | Field | or lines containing "Entity"
    lines = md_content.split('\n')
    
    current_entity = None
    
    for line in lines:
        line = line.strip()
        
        # Detect Entity Headers (e.g., "## 1. Stimulus Schema" or "### Stimulus")
        # We look for the entity name in the line
        if "Stimulus" in line and ("Schema" in line or "Entity" in line or line.startswith("#")):
            current_entity = "Stimulus"
            found_entities[current_entity] = []
        elif "Participant" in line and ("Schema" in line or "Entity" in line or line.startswith("#")):
            current_entity = "Participant"
            found_entities[current_entity] = []
        elif "Rating" in line and ("Schema" in line or "Entity" in line or line.startswith("#")):
            current_entity = "Rating"
            found_entities[current_entity] = []
        elif "AnalysisResult" in line and ("Schema" in line or "Entity" in line or line.startswith("#")):
            current_entity = "AnalysisResult"
            found_entities[current_entity] = []
        
        # Detect fields in markdown tables: | Field | Type | Description |
        if current_entity and line.startswith("|") and "Field" not in line:
            parts = line.split("|")
            if len(parts) >= 2:
                field_name = parts[1].strip()
                if field_name:
                    found_entities[current_entity].append(field_name)
                    
    return found_entities

def validate_schema(found: dict, reference: dict) -> tuple:
    """
    Compares found entities against the reference schema.
    Returns (is_valid, missing_fields_by_entity)
    """
    missing = {}
    is_valid = True

    for entity, required_fields in reference.items():
        if entity not in found:
            missing[entity] = required_fields
            is_valid = False
            continue
        
        found_fields = set(found[entity])
        required_set = set(required_fields)
        
        missing_fields = required_set - found_fields
        if missing_fields:
            missing[entity] = list(missing_fields)
            is_valid = False
    
    return is_valid, missing

def main():
    # Define paths relative to project root
    # Assuming this script is in code/ and project root is parent
    project_root = Path(__file__).resolve().parent.parent
    data_model_path = project_root / "specs" / "001-the-impact-of-text-message-tone-on-perce" / "data-model.md"

    # 1. Check existence
    if not data_model_path.exists():
        print(f"ERROR: Data model file not found at: {data_model_path}")
        print("Precondition failed: data-model.md MUST exist.")
        sys.exit(1)

    print(f"Found data model at: {data_model_path}")

    # 2. Read content
    try:
        content = data_model_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"ERROR: Could not read data model file: {e}")
        sys.exit(1)

    # 3. Extract entities
    found_entities = extract_entities_from_markdown(content)
    
    print("Detected entities in data-model.md:")
    for entity, fields in found_entities.items():
        print(f"  - {entity}: {len(fields)} fields")

    # 4. Validate against reference
    is_valid, missing = validate_schema(found_entities, REFERENCE_SCHEMA)

    if is_valid:
        print("\n[SUCCESS] Data model validation PASSED.")
        print("All required entities (Stimulus, Participant, Rating, AnalysisResult) and fields are present.")
        sys.exit(0)
    else:
        print("\n[FAILURE] Data model validation FAILED.")
        print("Missing fields detected in the following entities:")
        for entity, fields in missing.items():
            print(f"  - {entity}: {fields}")
        sys.exit(1)

if __name__ == "__main__":
    main()
