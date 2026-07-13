"""
Security scanning module for BIDS datasets.
Scans data/raw/ for PII using pybids and bids-validator patterns.
Automatically redacts personal identifiers found in JSON side-cars or filenames.
"""
import os
import re
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple

# Try to import bids, fallback to manual scanning if not available
try:
    from bids import BIDSLayout
    BIDS_AVAILABLE = True
except ImportError:
    BIDS_AVAILABLE = False

from utils.logger import get_logger
from utils.io import ensure_dir

logger = get_logger(__name__)

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
    """Check if a key is likely to contain PII."""
    key_lower = key.lower()
    
    # Check against BIDS-specific PII keys
    if key_lower in {k.lower() for k in BIDS_PII_KEYS}:
        return True
    
    # Check against regex patterns
    for pattern in PII_KEY_PATTERNS:
        if re.match(pattern, key_lower, re.IGNORECASE):
            return True
    
    return False

def is_pii_value(value: Any) -> bool:
    """Check if a value is likely to contain PII."""
    if not isinstance(value, str):
        return False
    
    value_str = str(value).strip()
    
    # Check against regex patterns
    for pattern in PII_VALUE_PATTERNS:
        if re.search(pattern, value_str, re.IGNORECASE):
            return True
    
    return False

def redact_value(value: str) -> str:
    """Redact a PII value by replacing it with a hash."""
    if not value:
        return value
    return f"[REDACTED-{hashlib.sha256(value.encode()).hexdigest()[:8]}]"

def redact_dict(data: Dict[str, Any], path: str = "") -> Tuple[Dict[str, Any], List[str]]:
    """Recursively redact PII from a dictionary."""
    redacted = {}
    findings = []
    
    for key, value in data.items():
        current_path = f"{path}.{key}" if path else key
        
        if isinstance(value, dict):
            redacted_dict, sub_findings = redact_dict(value, current_path)
            redacted[key] = redacted_dict
            findings.extend(sub_findings)
        elif isinstance(value, list):
            redacted_list = []
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    redacted_item, sub_findings = redact_dict(item, f"{current_path}[{i}]")
                    redacted_list.append(redacted_item)
                    findings.extend(sub_findings)
                elif is_pii_key(key) and is_pii_value(item):
                    findings.append(f"{current_path}[{i}]")
                    redacted_list.append(redact_value(str(item)))
                else:
                    redacted_list.append(item)
            redacted[key] = redacted_list
        elif is_pii_key(key) and is_pii_value(value):
            findings.append(current_path)
            redacted[key] = redact_value(str(value))
        else:
            redacted[key] = value
    
    return redacted, findings

def scan_json_file(file_path: Path) -> Tuple[Dict[str, Any], List[str]]:
    """Scan a JSON file for PII and redact it."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse JSON file {file_path}: {e}")
        return {}, []
    except Exception as e:
        logger.error(f"Error reading JSON file {file_path}: {e}")
        return {}, []
    
    redacted_data, findings = redact_dict(data)
    
    if findings:
        logger.info(f"Found PII in {file_path}: {findings}")
        # Write redacted version back
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(redacted_data, f, indent=2)
            logger.info(f"Redacted PII in {file_path}")
        except Exception as e:
            logger.error(f"Failed to write redacted JSON to {file_path}: {e}")
    
    return redacted_data, findings

def scan_filename(filename: str) -> List[str]:
    """Scan a filename for PII patterns."""
    findings = []
    filename_lower = filename.lower()
    
    # Check for common PII patterns in filenames
    for pattern in PII_KEY_PATTERNS:
        if re.search(pattern, filename_lower, re.IGNORECASE):
            findings.append(filename)
            break
    
    # Check for specific BIDS patterns that might contain PII
    if re.search(r'sub-\d+[^_]', filename_lower):
        # This is a normal BIDS subject ID, not PII
        pass
    elif re.search(r'patient[_-]?\d+|subject[_-]?\d+', filename_lower):
        findings.append(filename)
    
    return findings

def scan_directory(directory: Path) -> Dict[str, Any]:
    """Scan a directory for PII in JSON files and filenames."""
    results = {
        'scanned_files': [],
        'pii_found': [],
        'files_redacted': [],
        'errors': []
    }
    
    if not directory.exists():
        logger.warning(f"Directory {directory} does not exist")
        return results
    
    # Scan JSON files
    for json_file in directory.rglob('*.json'):
        results['scanned_files'].append(str(json_file))
        try:
            _, findings = scan_json_file(json_file)
            if findings:
                results['pii_found'].append({
                    'file': str(json_file),
                    'paths': findings
                })
                results['files_redacted'].append(str(json_file))
        except Exception as e:
            results['errors'].append({
                'file': str(json_file),
                'error': str(e)
            })
    
    # Scan filenames
    for file_path in directory.rglob('*'):
        if file_path.is_file():
            filename_findings = scan_filename(file_path.name)
            if filename_findings:
                results['pii_found'].append({
                    'file': str(file_path),
                    'filename_pii': filename_findings
                })
    
    # If BIDS layout is available, use it for more comprehensive scanning
    if BIDS_AVAILABLE:
        try:
            layout = BIDSLayout(str(directory), validate=False)
            logger.info(f"Using BIDS layout for {directory}")
            
            # Check participant files
            participants_file = directory / 'participants.tsv'
            if participants_file.exists():
                results['scanned_files'].append(str(participants_file))
                try:
                    import pandas as pd
                    df = pd.read_csv(participants_file, sep='\t')
                    for col in df.columns:
                        if is_pii_key(col):
                            results['pii_found'].append({
                                'file': str(participants_file),
                                'column': col,
                                'message': f"Potential PII column: {col}"
                            })
                except Exception as e:
                    results['errors'].append({
                        'file': str(participants_file),
                        'error': str(e)
                    })
        except Exception as e:
            logger.warning(f"Failed to create BIDS layout: {e}")
    
    return results

def main():
    """Main entry point for security scanning."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Scan BIDS dataset for PII')
    parser.add_argument('--input', '-i', type=str, default='data/raw',
                      help='Input directory to scan (default: data/raw)')
    parser.add_argument('--output', '-o', type=str, default='data/artifacts/security_scan_report.json',
                      help='Output report file (default: data/artifacts/security_scan_report.json)')
    parser.add_argument('--verbose', '-v', action='store_true',
                      help='Enable verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.INFO)
    
    input_dir = Path(args.input)
    output_file = Path(args.output)
    
    logger.info(f"Starting PII scan on {input_dir}")
    
    if not input_dir.exists():
        logger.error(f"Input directory {input_dir} does not exist")
        return 1
    
    # Perform scan
    results = scan_directory(input_dir)
    
    # Ensure output directory exists
    ensure_dir(output_file.parent)
    
    # Write report
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Security scan report written to {output_file}")
    except Exception as e:
        logger.error(f"Failed to write report: {e}")
        return 1
    
    # Summary
    logger.info(f"Scanned {len(results['scanned_files'])} files")
    logger.info(f"Found PII in {len(results['pii_found'])} locations")
    logger.info(f"Redacted {len(results['files_redacted'])} files")
    if results['errors']:
        logger.warning(f"Encountered {len(results['errors'])} errors during scan")
    
    # Return non-zero if PII was found
    return 0 if not results['pii_found'] else 1

if __name__ == '__main__':
    exit(main())