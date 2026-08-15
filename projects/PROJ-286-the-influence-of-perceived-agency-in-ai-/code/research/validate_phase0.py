"""
Task T003: Validate research.md and research/power_calculation.json against plan.md Phase 0 requirements.

This script validates that the Phase 0 artifacts (research.md and power_calculation.json)
contain the required fields and structure as specified in the project plan.
"""
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


def load_json_file(path: str) -> Dict[str, Any]:
    """Load and parse a JSON file."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Required file not found: {path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {path}: {e}")


def read_text_file(path: str) -> str:
    """Read the contents of a text file."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Required file not found: {path}")


def validate_power_calculation_json(data: Dict[str, Any]) -> List[str]:
    """
    Validate the structure of power_calculation.json.
    Returns a list of error messages. Empty list means valid.
    """
    errors = []
    required_keys = ['effect_size', 'alpha', 'target_power', 'required_n', 'calculated_n', 'test_type']
    
    for key in required_keys:
        if key not in data:
            errors.append(f"Missing required key in power_calculation.json: {key}")
    
    # Validate types if keys exist
    if 'required_n' in data and not isinstance(data['required_n'], (int, float)):
        errors.append("power_calculation.json: 'required_n' must be a number")
    
    if 'calculated_n' in data and not isinstance(data['calculated_n'], (int, float)):
        errors.append("power_calculation.json: 'calculated_n' must be a number")
    
    if 'effect_size' in data and not isinstance(data['effect_size'], (int, float)):
        errors.append("power_calculation.json: 'effect_size' must be a number")
    
    if 'alpha' in data and not isinstance(data['alpha'], (int, float)):
        errors.append("power_calculation.json: 'alpha' must be a number")
    
    if 'target_power' in data and not isinstance(data['target_power'], (int, float)):
        errors.append("power_calculation.json: 'target_power' must be a number")
    
    return errors


def validate_citations_json(data: Dict[str, Any]) -> List[str]:
    """
    Validate the structure of validation_report.json.
    Returns a list of error messages. Empty list means valid.
    """
    errors = []
    if not isinstance(data, list):
        errors.append("validation_report.json must be a list of citation objects")
        return errors
    
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            errors.append(f"validation_report.json: Item {i} must be a dictionary")
            continue
        
        required_keys = ['title', 'doi', 'overlap_score', 'status']
        for key in required_keys:
            if key not in item:
                errors.append(f"validation_report.json: Item {i} missing key '{key}'")
        
        if 'overlap_score' in item and not isinstance(item['overlap_score'], (int, float)):
            errors.append(f"validation_report.json: Item {i} 'overlap_score' must be a number")
        
        if 'status' in item and item['status'] not in ['valid', 'invalid']:
            errors.append(f"validation_report.json: Item {i} 'status' must be 'valid' or 'invalid'")
    
    return errors


def validate_citation_log(content: str) -> List[str]:
    """
    Validate the structure of citation_verification_log.md.
    Returns a list of error messages. Empty list means valid.
    """
    errors = []
    if not content.strip():
        errors.append("citation_verification_log.md is empty")
        return errors
    
    # Check for required sections or status indicators
    if "status=" not in content and "Status:" not in content:
        errors.append("citation_verification_log.md must contain a status indicator")
    
    return errors


def validate_research_md(content: str, power_data: Dict[str, Any]) -> List[str]:
    """
    Validate research.md contains the required table and content.
    Returns a list of error messages. Empty list means valid.
    """
    errors = []
    
    # Check for required table headers
    required_headers = ['Effect Size', 'Alpha', 'Target Power', 'Required N', 'Calculated N']
    
    # Check if all headers are present in the content
    content_lower = content.lower()
    for header in required_headers:
        if header.lower() not in content_lower:
            errors.append(f"research.md missing required table header: {header}")
    
    # Check for a markdown table structure (simple heuristic)
    if '|' not in content:
        errors.append("research.md does not appear to contain a markdown table")
    
    # Verify that the values in the table match power_calculation.json
    # We look for the numeric values in the content
    if 'required_n' in power_data:
        required_n_str = str(int(power_data['required_n']))
        if required_n_str not in content:
            errors.append(f"research.md does not contain the required_n value: {power_data['required_n']}")
    
    if 'calculated_n' in power_data:
        calculated_n_str = str(int(power_data['calculated_n']))
        if calculated_n_str not in content:
            errors.append(f"research.md does not contain the calculated_n value: {power_data['calculated_n']}")
    
    return errors


def main():
    """Main entry point for Phase 0 validation."""
    project_root = Path(__file__).parent.parent.parent
    
    # Define paths
    power_calc_path = project_root / 'research' / 'power_calculation.json'
    research_md_path = project_root / 'specs' / '001-perceived-agency-trust' / 'research.md'
    validation_report_path = project_root / 'research' / 'validation_report.json'
    citation_log_path = project_root / 'research' / 'citation_verification_log.md'
    
    all_errors = []
    validation_status = "PASSED"
    
    print("=== Phase 0 Validation Report ===\n")
    
    # 1. Validate power_calculation.json
    print(f"Validating: {power_calc_path}")
    try:
        power_data = load_json_file(str(power_calc_path))
        power_errors = validate_power_calculation_json(power_data)
        if power_errors:
            all_errors.extend(power_errors)
            print(f"  ❌ FAILED: {len(power_errors)} errors found")
            for err in power_errors:
                print(f"     - {err}")
        else:
            print("  ✅ PASSED")
    except Exception as e:
        all_errors.append(f"Error loading {power_calc_path}: {e}")
        print(f"  ❌ FAILED: {e}")
    
    # 2. Validate research.md
    print(f"\nValidating: {research_md_path}")
    try:
        research_content = read_text_file(str(research_md_path))
        if power_data:  # Only validate if we have power data
            md_errors = validate_research_md(research_content, power_data)
        else:
            md_errors = ["Cannot validate research.md without valid power_calculation.json"]
        
        if md_errors:
            all_errors.extend(md_errors)
            print(f"  ❌ FAILED: {len(md_errors)} errors found")
            for err in md_errors:
                print(f"     - {err}")
        else:
            print("  ✅ PASSED")
    except Exception as e:
        all_errors.append(f"Error loading {research_md_path}: {e}")
        print(f"  ❌ FAILED: {e}")
    
    # 3. Validate validation_report.json (from T000b)
    print(f"\nValidating: {validation_report_path}")
    try:
        citation_data = load_json_file(str(validation_report_path))
        citation_errors = validate_citations_json(citation_data)
        if citation_errors:
            all_errors.extend(citation_errors)
            print(f"  ❌ FAILED: {len(citation_errors)} errors found")
            for err in citation_errors:
                print(f"     - {err}")
        else:
            print("  ✅ PASSED")
    except Exception as e:
        all_errors.append(f"Error loading {validation_report_path}: {e}")
        print(f"  ❌ FAILED: {e}")
    
    # 4. Validate citation_verification_log.md (from T000c)
    print(f"\nValidating: {citation_log_path}")
    try:
        log_content = read_text_file(str(citation_log_path))
        log_errors = validate_citation_log(log_content)
        if log_errors:
            all_errors.extend(log_errors)
            print(f"  ❌ FAILED: {len(log_errors)} errors found")
            for err in log_errors:
                print(f"     - {err}")
        else:
            print("  ✅ PASSED")
    except Exception as e:
        all_errors.append(f"Error loading {citation_log_path}: {e}")
        print(f"  ❌ FAILED: {e}")
    
    # Final Summary
    print("\n=== Validation Summary ===")
    if all_errors:
        print(f"❌ VALIDATION FAILED: {len(all_errors)} total errors")
        validation_status = "FAILED"
        sys.exit(1)
    else:
        print("✅ VALIDATION PASSED: All Phase 0 requirements met")
        validation_status = "PASSED"
        sys.exit(0)


if __name__ == "__main__":
    main()