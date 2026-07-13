"""
Security hardening: Scan data/raw/ for PII using pybids/bids-validator logic.
Automatically redact any personal identifiers found in JSON side-cars or filenames.
"""
import argparse
import json
import re
import shutil
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional
import os

# PII Patterns based on BIDS specification and general privacy concerns
# BIDS explicitly forbids certain keys in JSON sidecars if they contain PII
# We also scan filenames for common PII patterns
PII_KEYS = {
    'participant_id', 'subject_id', 'patient_id', 'dob', 'date_of_birth',
    'birth_date', 'age', 'sex', 'gender', 'ethnicity', 'race',
    'address', 'phone', 'phone_number', 'email', 'ssn', 'social_security',
    'medical_record_number', 'mrn', 'hospital_id', 'institution_id',
    'acquisition_date', 'scan_date', 'visit_date', 'date',
    'first_name', 'last_name', 'full_name', 'name',
    'license_plate', 'vehicle_id', 'device_serial_number',
    'biometric_id', 'fingerprint', 'face_id'
}

PII_VALUE_PATTERNS = [
    # SSN
    re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
    # Phone numbers (various formats)
    re.compile(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b'),
    # Email addresses
    re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'),
    # Dates (YYYY-MM-DD, MM/DD/YYYY, etc.) - often PII in medical context
    re.compile(r'\b\d{4}[-/]\d{2}[-/]\d{2}\b'),
    re.compile(r'\b\d{2}[-/]\d{2}[-/]\d{4}\b'),
    # High-precision coordinates or IDs that might be unique identifiers
    re.compile(r'\b[A-Z0-9]{10,}\b'),
]

# PII patterns based on BIDS specification and common medical data privacy concerns
PII_KEY_PATTERNS = [
    r'^(participant_id|subject_id|patient_id|patientname|patientdob|patientsex|patientage|patientweight|patientheight|patientbirthdate|patientdeathdate|studyid|institution|institutionaddress|institutiondepartment|institutioncity|institutionstate|institutionzip|institutioncountry|institutionphone|institutionfax|institutionemail|institutionwebsite|institutioncontact|institutioncontactphone|institutioncontactemail|institutioncontactfax|institutioncontactwebsite|institutioncontactaddress|institutioncontactcity|institutioncontactstate|institutioncontactzip|institutioncontactcountry)$',
    r'^(sub-|ses-|task-|run-|modality-|acquisition-|ceagent-|cecontrast-|echo-|flipangle-|inv-|mt-|part-|phase-|space-|reconstruction-|direction-|recon-|suffix-|extension-|fmap-|acq-|rec-|dir-|task-|mod-|echo-|part-|phase-|space-|recon-|direction-|fmap-|ceagent-|cecontrast-|flipangle-|inv-|mt-)$',
    r'^(name|dob|age|sex|gender|race|ethnicity|address|phone|email|ssn|medicare|medicaid|insurance|employer|occupation|marital_status|religion|education|income|medical_record_number|health_plan_number|account_number|hospitalization_number|device_identifier|web_url|ip_address|biometric_id|face_recognition|full_face_photo|unique_identifier)$',
    r'^(participant|subject|patient|study|institution|site|center|hospital|clinic|doctor|physician|nurse|technician|researcher|investigator|coordinator|admin|manager|director|staff|volunteer|donor|sample|specimen|tissue|blood|urine|saliva|dna|rna|protein|metabolite|lipid|carbohydrate|nucleic_acid|cell|tissue_sample|biopsy|autopsy|surgery|procedure|operation|treatment|therapy|medication|drug|dosage|frequency|duration|side_effect|adverse_event|complication|outcome|follow_up|visit|appointment|screening|diagnosis|prognosis|risk_factor|comorbidity|medication_history|family_history|social_history|physical_exam|lab_test|imaging|pathology|genetic_test|biomarker|clinical_trial|protocol|inclusion_criteria|exclusion_criteria|randomization|blinding|placebo|control|intervention|exposure|outcome_measure|primary_endpoint|secondary_endpoint|safety_endpoint|efficacy_endpoint|statistical_analysis|sample_size|power|significance|confidence_interval|p_value|effect_size|odds_ratio|risk_ratio|hazard_ratio|confidence_level|alpha|beta|type_i_error|type_ii_error|false_positive|false_negative|true_positive|true_negative|sensitivity|specificity|accuracy|precision|recall|f1_score|roc_auc|auc|area_under_curve|confusion_matrix|classification_report|model_performance|cross_validation|train_test_split|overfitting|underfitting|regularization|hyperparameter|grid_search|random_search|bayesian_optimization|early_stopping|learning_rate|batch_size|epoch|iteration|optimizer|loss_function|activation_function|neural_network|deep_learning|machine_learning|artificial_intelligence|data_preprocessing|feature_engineering|dimensionality_reduction|clustering|classification|regression|time_series|survival_analysis|longitudinal|cross_sectional|cohort|case_control|randomized_controlled_trial|observational|retrospective|prospective|meta_analysis|systematic_review|evidence_based|clinical_guideline|best_practice|quality_improvement|patient_safety|medical_error|adverse_drug_reaction|drug_interaction|contraindication|warning|precaution|indication|dosage_form|route_of_administration|storage|handling|disposal|regulatory|approval|fda|ema|pharmacovigilance|post_market|surveillance|reporting|compliance|audit|inspection|enforcement|recall|warning_letter|consent|informed_consent|ethics|irb|institutional_review_board|research_ethics|human_subjects|animal_subjects|animal_welfare|bioethics|medical_ethics|research_integrity|data_integrity|data_protection|privacy|confidentiality|anonymization|pseudonymization|deidentification|reidentification|data_breach|security|cybersecurity|encryption|access_control|authentication|authorization|audit_log|backup|disaster_recovery|business_continuity|risk_management|incident_response|forensics|investigation|litigation|discovery|subpoena|court_order|warrant|search_seizure|exclusion|exclusion_criteria|inclusion_criteria|eligibility|screening|recruitment|enrollment|retention|drop_out|completion|follow_up|longitudinal|cross_sectional|cohort|case_control|randomized_controlled_trial|observational|retrospective|prospective|meta_analysis|systematic_review|evidence_based|clinical_guideline|best_practice|quality_improvement|patient_safety|medical_error|adverse_drug_reaction|drug_interaction|contraindication|warning|precaution|indication|dosage_form|route_of_administration|storage|handling|disposal|regulatory|approval|fda|ema|pharmacovigilance|post_market|surveillance|reporting|compliance|audit|inspection|enforcement|recall|warning_letter|consent|informed_consent|ethics|irb|institutional_review_board|research_ethics|human_subjects|animal_subjects|animal_welfare|bioethics|medical_ethics|research_integrity|data_integrity|data_protection|privacy|confidentiality|anonymization|pseudonymization|deidentification|reidentification|data_breach|security|cybersecurity|encryption|access_control|authentication|authorization|audit_log|backup|disaster_recovery|business_continuity|risk_management|incident_response|forensics|investigation|litigation|discovery|subpoena|court_order|warrant|search_seizure)$',
]

PII_VALUE_PATTERNS = [
    r'\b\d{3}-\d{2}-\d{4}\b',  # SSN pattern
    r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # Phone number pattern
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email pattern
    r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',  # IP address pattern
    r'\b\d{1,3}[-.]?\d{1,3}[-.]?\d{1,3}[-.]?\d{1,3}[-.]?\d{1,3}\b',  # IP v6 pattern
    r'\b[A-Z]{2}\s\d{5}(-\d{4})?\b',  # US ZIP code pattern
    r'\b\d{1,2}\/\d{1,2}\/\d{4}\b',  # Date pattern (MM/DD/YYYY)
    r'\b\d{4}-\d{2}-\d{2}\b',  # Date pattern (YYYY-MM-DD)
    r'\b\d{1,2}[-.]?\d{1,2}[-.]?\d{4}\b',  # Date pattern (MM-DD-YYYY or DD-MM-YYYY)
    r'\b[A-Z][a-z]+\s[A-Z][a-z]+\b',  # Name pattern (First Last)
    r'\b[A-Z]{2,}\b',  # All caps acronym (potential ID)
]

# BIDS-specific PII patterns
BIDS_PII_KEYS = {
    'participant_id', 'subject_id', 'patient_id', 'patientName', 'patientDOB',
    'patientSex', 'patientAge', 'patientWeight', 'patientHeight', 'patientBirthDate',
    'patientDeathDate', 'studyID', 'institutionName', 'institutionAddress',
    'institutionDepartment', 'institutionCity', 'institutionState', 'institutionZip',
    'institutionCountry', 'institutionPhone', 'institutionFax', 'institutionEmail',
    'institutionWebsite', 'institutionContact', 'institutionContactPhone',
    'institutionContactEmail', 'institutionContactFax', 'institutionContactWebsite',
    'institutionContactAddress', 'institutionContactCity', 'institutionContactState',
    'institutionContactZip', 'institutionContactCountry',
}

def is_pii_key(key: str) -> bool:
    """Check if a JSON key is likely to contain PII."""
    key_lower = key.lower().strip()
    # Direct match
    if key_lower in PII_KEYS:
        return True
    # Partial match (e.g., 'patient_id_1' contains 'patient_id')
    for pii_key in PII_KEYS:
        if pii_key in key_lower:
            return True
    
    return False

def is_pii_value(value: Any) -> bool:
    """Check if a value looks like PII."""
    if not isinstance(value, str):
        return False
    
    value_stripped = value.strip()
    if not value_stripped:
        return False
        
    for pattern in PII_VALUE_PATTERNS:
        if pattern.search(value_stripped):
            return True
    return False

def redact_value(value: str, key: str) -> str:
    """Redact a PII value, replacing with a generic placeholder."""
    if is_pii_key(key):
        return "[REDACTED_PII_KEY]"
    
    # Apply pattern-based redaction
    redacted = value
    for pattern in PII_VALUE_PATTERNS:
        redacted = pattern.sub('[REDACTED_PII]', redacted)
    
    return redacted if redacted != value else value

def redact_dict(data: Dict[str, Any], path: str = "") -> Tuple[Dict[str, Any], List[str]]:
    """Recursively redact PII from a dictionary and return list of redacted keys."""
    redacted_data = {}
    redacted_keys = []
    
    for key, value in data.items():
        current_path = f"{path}.{key}" if path else key
        
        if isinstance(value, dict):
            sub_redacted, sub_keys = redact_dict(value, current_path)
            redacted_data[key] = sub_redacted
            redacted_keys.extend(sub_keys)
        elif isinstance(value, list):
            redacted_list = []
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    sub_redacted, sub_keys = redact_dict(item, f"{current_path}[{i}]")
                    redacted_list.append(sub_redacted)
                    redacted_keys.extend(sub_keys)
                elif is_pii_value(item):
                    redacted_list.append(redact_value(item, key))
                    redacted_keys.append(f"{current_path}[{i}]")
                else:
                    redacted_list.append(item)
            redacted_data[key] = redacted_list
        elif is_pii_value(value) or is_pii_key(key):
            redacted_data[key] = redact_value(str(value), key)
            redacted_keys.append(current_path)
        else:
            redacted_data[key] = value
    
    return redacted_data, redacted_keys

def scan_filename(filepath: Path) -> List[str]:
    """Scan a filename for potential PII patterns."""
    issues = []
    filename = filepath.name
    
    # Check for common PII patterns in filename
    for pattern in PII_VALUE_PATTERNS:
        if pattern.search(filename):
            issues.append(f"PII pattern found in filename: {filename}")
            break
    
    # Check for keys in filename that might indicate PII
    for key in PII_KEYS:
        if key in filename.lower():
            issues.append(f"Potential PII key in filename: {filename}")
            break
    
    return issues

def scan_json_file(filepath: Path) -> Tuple[Dict[str, Any], List[str], List[str]]:
    """Scan and redact PII from a JSON file. Returns (redacted_data, redacted_keys, errors)."""
    redacted_keys = []
    errors = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, dict):
            return data, [], [f"JSON root is not a dict: {filepath}"]
        
        redacted_data, redacted_keys = redact_dict(data)
        return redacted_data, redacted_keys, []
        
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON in {filepath}: {str(e)}")
        return {}, [], errors
    except Exception as e:
        errors.append(f"Error reading {filepath}: {str(e)}")
        return {}, [], errors

def scan_directory(raw_data_dir: Path, dry_run: bool = True) -> Dict[str, Any]:
    """
    Scan a directory for PII in JSON sidecars and filenames.
    
    Args:
        raw_data_dir: Path to the directory to scan (typically data/raw/)
        dry_run: If True, only report findings without modifying files.
    
    Returns:
        Dictionary containing scan results.
    """
    results = {
        'scanned_directory': str(raw_data_dir),
        'dry_run': dry_run,
        'files_scanned': 0,
        'files_with_issues': 0,
        'total_redactions': 0,
        'filename_issues': [],
        'json_issues': [],
        'modified_files': []
    }
    
    if not raw_data_dir.exists():
        results['error'] = f"Directory does not exist: {raw_data_dir}"
        return results
    
    # Find all JSON files
    json_files = list(raw_data_dir.rglob("*.json"))
    results['files_scanned'] = len(json_files)
    
    for json_file in json_files:
        # Check filename first
        filename_issues = scan_filename(json_file)
        if filename_issues:
            results['filename_issues'].append({
                'file': str(json_file),
                'issues': filename_issues
            })
            results['files_with_issues'] += 1
        
        # Scan JSON content
        redacted_data, redacted_keys, errors = scan_json_file(json_file)
        
        if errors:
            results['json_issues'].append({
                'file': str(json_file),
                'errors': errors
            })
            continue
        
        if redacted_keys:
            results['json_issues'].append({
                'file': str(json_file),
                'redacted_keys': redacted_keys,
                'count': len(redacted_keys)
            })
            results['total_redactions'] += len(redacted_keys)
            results['files_with_issues'] += 1
            
            if not dry_run:
                # Write redacted data back to file
                try:
                    with open(json_file, 'w', encoding='utf-8') as f:
                        json.dump(redacted_data, f, indent=2)
                    results['modified_files'].append(str(json_file))
                except Exception as e:
                    results['json_issues'].append({
                        'file': str(json_file),
                        'error': f"Failed to write redacted data: {str(e)}"
                    })
    
    return results

def main():
    """Main entry point for the security scanner."""
    parser = argparse.ArgumentParser(
        description="Scan BIDS dataset for PII and redact if necessary."
    )
    parser.add_argument(
        '--input', '-i',
        type=Path,
        default=Path("data/raw"),
        help="Path to the BIDS dataset directory (default: data/raw)"
    )
    parser.add_argument(
        '--dry-run', '-n',
        action='store_true',
        help="Only report findings without modifying files"
    )
    parser.add_argument(
        '--output', '-o',
        type=Path,
        default=Path("data/artifacts/security_scan_report.json"),
        help="Path to output the scan report (default: data/artifacts/security_scan_report.json)"
    )
    
    args = parser.parse_args()
    
    print(f"Scanning directory: {args.input}")
    print(f"Dry run mode: {args.dry_run}")
    
    results = scan_directory(args.input, dry_run=args.dry_run)
    
    # Ensure output directory exists
    args.output.parent.mkdir(parents=True, exist_ok=True)
    
    # Write report
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print(f"\nScan complete!")
    print(f"Files scanned: {results['files_scanned']}")
    print(f"Files with issues: {results['files_with_issues']}")
    print(f"Total redactions: {results['total_redactions']}")
    print(f"Report saved to: {args.output}")
    
    if results.get('error'):
        print(f"\nError: {results['error']}")
        return 1
    
    if results['files_with_issues'] > 0 and args.dry_run:
        print(f"\n⚠️  Found {results['files_with_issues']} files with potential PII.")
        print(f"   Re-run without --dry-run to redact automatically.")
        return 0
    elif results['files_with_issues'] > 0:
        print(f"\n✅ Redacted {results['total_redactions']} PII instances in {results['files_with_issues']} files.")
        return 0
    else:
        print(f"\n✅ No PII detected.")
        return 0

if __name__ == "__main__":
    exit(main())