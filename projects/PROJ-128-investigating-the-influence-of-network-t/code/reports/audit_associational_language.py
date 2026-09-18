import os
import json
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple

# List of causality-implying verbs and phrases to flag
CAUSAL_PATTERNS = [
    r'\bpredicts?\b',
    r'\bcaus(e|ation|al)\b',
    r'\bdetermin(e|es|ing)\b',
    r'\bdirect(e|s|ly)\b',
    r'\bdrive(s|d|ing)\b',
    r'\binfluence(s|d|ing)\b',
    r'\bgovern(s|ed|ing)\b',
    r'\bcontrol(s|ed|ing)\b',
    r'\bmediate(s|d|ing)\b',
    r'\bmoderate(s|d|ing)\b',
    r'\bmechanism\b',
    r'\bunderlie(s|d|ing)\b',
    r'\bresult(s|ed|ing) in\b',
    r'\blead(s|ed|ing) to\b',
    r'\btrigger(s|ed|ing)\b',
    r'\bgenerate(s|d|ing)\b',
    r'\bproduce(s|d|ing)\b',
    r'\bcause(s|d|ing)\b',
]

# Contexts where these words are acceptable (e.g., "predictive modeling")
SAFE_CONTEXTS = [
    r'\bpredictive\s+modeling\b',
    r'\bpredictive\s+power\b',
    r'\bpredictive\s+value\b',
    r'\bpredictive\s+accuracy\b',
    r'\bpredictive\s+validity\b',
    r'\bpredictive\s+relationship\b',
    r'\bpredictive\s+association\b',
    r'\bpredictive\s+capacity\b',
    r'\bpredictive\s+factor\b',
    r'\bpredictive\s+utility\b',
    r'\bpredictive\s+performance\b',
    r'\bpredictive\s+potential\b',
    r'\bpredictive\s+indicator\b',
    r'\bpredictive\s+signature\b',
    r'\bpredictive\s+pattern\b',
    r'\bpredictive\s+signal\b',
    r'\bpredictive\s+feature\b',
    r'\bpredictive\s+variable\b',
    r'\bpredictive\s+metric\b',
    r'\bpredictive\s+parameter\b',
    r'\bpredictive\s+estimate\b',
    r'\bpredictive\s+score\b',
    r'\bpredictive\s+index\b',
    r'\bpredictive\s+measure\b',
    r'\bpredictive\s+statistic\b',
    r'\bpredictive\s+correlation\b',
    r'\bpredictive\s+coefficient\b',
    r'\bpredictive\s+relationship\b',
    r'\bpredictive\s+association\b',
    r'\bpredictive\s+link\b',
    r'\bpredictive\s+connection\b',
    r'\bpredictive\s+relation\b',
    r'\bpredictive\s+dependence\b',
    r'\bpredictive\s+dependency\b',
    r'\bpredictive\s+correspondence\b',
    r'\bpredictive\s+correlation\b',
    r'\bpredictive\s+association\b',
    r'\bpredictive\s+relationship\b',
    r'\bpredictive\s+link\b',
    r'\bpredictive\s+connection\b',
    r'\bpredictive\s+relation\b',
    r'\bpredictive\s+dependence\b',
    r'\bpredictive\s+dependency\b',
    r'\bpredictive\s+correspondence\b',
    r'\bassociational\s+language\b',
    r'\bassociational\s+framing\b',
    r'\bassociational\s+study\b',
    r'\bassociational\s+analysis\b',
    r'\bassociational\s+finding\b',
    r'\bassociational\s+result\b',
    r'\bassociational\s+evidence\b',
    r'\bassociational\s+data\b',
    r'\bassociational\s+correlation\b',
    r'\bassociational\s+relationship\b',
    r'\bassociational\s+link\b',
    r'\bassociational\s+connection\b',
    r'\bassociational\s+relation\b',
    r'\bassociational\s+dependence\b',
    r'\bassociational\s+dependency\b',
    r'\bassociational\s+correspondence\b',
    r'\bassociational\s+pattern\b',
    r'\bassociational\s+trend\b',
    r'\bassociational\s+association\b',
    r'\bassociational\s+co-occurrence\b',
    r'\bassociational\s+co-variance\b',
    r'\bassociational\s+co-relation\b',
    r'\bassociational\s+co-variation\b',
    r'\bassociational\s+co-dependence\b',
    r'\bassociational\s+co-dependency\b',
    r'\bassociational\s+co-correspondence\b',
    r'\bassociational\s+co-pattern\b',
    r'\bassociational\s+co-trend\b',
    r'\bassociational\s+co-association\b',
    r'\bassociational\s+co-occurrence\b',
    r'\bassociational\s+co-variance\b',
    r'\bassociational\s+co-relation\b',
    r'\bassociational\s+co-variation\b',
    r'\bassociational\s+co-dependence\b',
    r'\bassociational\s+co-dependency\b',
    r'\bassociational\s+co-correspondence\b',
    r'\bassociational\s+co-pattern\b',
    r'\bassociational\s+co-trend\b',
    r'\bassociational\s+co-association\b',
]

def load_json_file(filepath: str) -> Optional[Dict[str, Any]]:
    """Load a JSON file and return its contents as a dictionary."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON file {filepath}: {e}")
        return None

def load_csv_file(filepath: str) -> Optional[List[Dict[str, Any]]]:
    """Load a CSV file and return its contents as a list of dictionaries."""
    try:
        import pandas as pd
        df = pd.read_csv(filepath)
        return df.to_dict(orient='records')
    except Exception as e:
        print(f"Error loading CSV file {filepath}: {e}")
        return None

def check_text_for_causality(text: str) -> List[Tuple[str, str]]:
    """
    Check text for causality-implying language.
    Returns a list of tuples (pattern, matched_text).
    """
    if not text or not isinstance(text, str):
        return []

    matches = []
    text_lower = text.lower()

    for pattern in CAUSAL_PATTERNS:
        # Check if the pattern exists in the text
        if re.search(pattern, text_lower):
            # Check if it's in a safe context
            safe_context_found = False
            for safe_pattern in SAFE_CONTEXTS:
                if re.search(safe_pattern, text_lower):
                    safe_context_found = True
                    break

            if not safe_context_found:
                # Find the actual matched text
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    matches.append((pattern, match.group()))

    return matches

def scan_report_json(filepath: str) -> Dict[str, Any]:
    """
    Scan a JSON report file for causality-implying language.
    Returns a dictionary with findings.
    """
    data = load_json_file(filepath)
    if data is None:
        return {"error": f"Could not load file: {filepath}"}

    findings = []
    text_fields = ['title', 'abstract', 'summary', 'conclusion', 'discussion', 'interpretation',
                   'recommendation', 'implication', 'finding', 'result', 'observation',
                   'hypothesis', 'theory', 'model', 'method', 'approach', 'technique',
                   'analysis', 'result', 'output', 'metric', 'value', 'description',
                   'interpretation', 'conclusion', 'summary', 'abstract', 'title']

    def traverse(obj, path=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                traverse(value, f"{path}.{key}" if path else key)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                traverse(item, f"{path}[{i}]")
        elif isinstance(obj, str):
            matches = check_text_for_causality(obj)
            if matches:
                for pattern, matched_text in matches:
                    findings.append({
                        "field": path,
                        "pattern": pattern,
                        "matched_text": matched_text,
                        "full_text": obj[:200] + "..." if len(obj) > 200 else obj
                    })

    traverse(data)

    return {
        "file": filepath,
        "findings": findings,
        "total_findings": len(findings),
        "status": "non-compliant" if findings else "compliant"
    }

def scan_csv_file(filepath: str) -> Dict[str, Any]:
    """
    Scan a CSV file for causality-implying language in text fields.
    Returns a dictionary with findings.
    """
    data = load_csv_file(filepath)
    if data is None:
        return {"error": f"Could not load file: {filepath}"}

    findings = []
    text_columns = ['description', 'interpretation', 'conclusion', 'summary', 'notes',
                    'comments', 'remarks', 'analysis', 'result', 'observation',
                    'finding', 'implication', 'recommendation', 'hypothesis', 'theory']

    for i, row in enumerate(data):
        for col in text_columns:
            if col in row and isinstance(row[col], str):
                matches = check_text_for_causality(row[col])
                if matches:
                    for pattern, matched_text in matches:
                        findings.append({
                            "row": i,
                            "column": col,
                            "pattern": pattern,
                            "matched_text": matched_text,
                            "full_text": row[col][:200] + "..." if len(row[col]) > 200 else row[col]
                        })

    return {
        "file": filepath,
        "findings": findings,
        "total_findings": len(findings),
        "status": "non-compliant" if findings else "compliant"
    }

def generate_audit_report(report_dir: str, output_path: str) -> Dict[str, Any]:
    """
    Generate a comprehensive audit report for all files in the report directory.
    """
    report_path = Path(report_dir)
    if not report_path.exists():
        return {"error": f"Report directory not found: {report_dir}"}

    all_findings = []
    file_results = []

    # Scan JSON files
    json_files = list(report_path.glob("*.json"))
    for json_file in json_files:
        result = scan_report_json(str(json_file))
        file_results.append(result)
        if "findings" in result:
            all_findings.extend(result["findings"])

    # Scan CSV files
    csv_files = list(report_path.glob("*.csv"))
    for csv_file in csv_files:
        result = scan_csv_file(str(csv_file))
        file_results.append(result)
        if "findings" in result:
            all_findings.extend(result["findings"])

    # Generate summary
    total_files = len(file_results)
    compliant_files = sum(1 for r in file_results if r.get("status") == "compliant")
    non_compliant_files = total_files - compliant_files

    audit_summary = {
        "report_directory": report_dir,
        "total_files_scanned": total_files,
        "compliant_files": compliant_files,
        "non_compliant_files": non_compliant_files,
        "total_causality_findings": len(all_findings),
        "overall_status": "non-compliant" if non_compliant_files > 0 else "compliant",
        "file_results": file_results,
        "detailed_findings": all_findings
    }

    # Save the audit report
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(audit_summary, f, indent=2)

    return audit_summary

def main():
    """
    Main function to run the associational language audit.
    """
    # Default paths
    report_dir = "data/reports"
    output_path = "data/reports/associational_language_audit.json"

    # Allow command line arguments
    if len(sys.argv) > 1:
        report_dir = sys.argv[1]
    if len(sys.argv) > 2:
        output_path = sys.argv[2]

    print(f"Scanning report directory: {report_dir}")
    print(f"Output will be saved to: {output_path}")

    result = generate_audit_report(report_dir, output_path)

    print("\n--- Audit Summary ---")
    print(f"Total files scanned: {result.get('total_files_scanned', 0)}")
    print(f"Compliant files: {result.get('compliant_files', 0)}")
    print(f"Non-compliant files: {result.get('non_compliant_files', 0)}")
    print(f"Total causality findings: {result.get('total_causality_findings', 0)}")
    print(f"Overall status: {result.get('overall_status', 'unknown')}")

    if result.get('detailed_findings'):
        print("\n--- Detailed Findings ---")
        for finding in result['detailed_findings'][:10]:  # Show first 10
            print(f"  - File: {finding.get('file', 'N/A')}, Field: {finding.get('field', finding.get('column', 'N/A'))}")
            print(f"    Pattern: {finding.get('pattern', 'N/A')}")
            print(f"    Matched: {finding.get('matched_text', 'N/A')}")
            print()

    print(f"Audit report saved to: {output_path}")
    return result

if __name__ == "__main__":
    main()
