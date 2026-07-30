"""
Preprocessing module for parsing raw vulnerability datasets.
Extracts code snippets, preserves language fields, and handles edge cases.
"""
import os
import json
import csv
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any

from src.models.code_snippet import CodeSnippet, create_snippet
from src.utils.logger import get_logger
from src.utils.config import get_project_root

logger = get_logger("preprocess")

# Language extension mapping
EXT_TO_LANG = {
    ".py": "Python",
    ".c": "C",
    ".cpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".h": "C/C++",
    ".hpp": "C++",
    ".java": "Java",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".go": "Go",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".php": "PHP",
}

# Vulnerability category normalization map
LABEL_MAP = {
    "sql": "SQLi",
    "sql injection": "SQLi",
    "injection": "SQLi",
    "buffer overflow": "Buffer Overflow",
    "overflow": "Buffer Overflow",
    "xss": "XSS",
    "cross-site scripting": "XSS",
    "rce": "RCE",
    "remote code execution": "RCE",
    "command injection": "Command Injection",
    "path traversal": "Path Traversal",
    "arbitrary file access": "Path Traversal",
    "none": "none",
    "safe": "none",
    "no vulnerability": "none",
    "vulnerable": "vulnerable",
    "unknown": "unknown",
    "uncertain": "uncertain",
}

def detect_language_from_extension(file_path: str) -> Optional[str]:
    """Detect programming language from file extension."""
    ext = Path(file_path).suffix.lower()
    return EXT_TO_LANG.get(ext)

def normalize_label(label: Optional[str]) -> Optional[str]:
    """Normalize ground-truth label to canonical category."""
    if not label:
        return None
    normalized = label.lower().strip()
    return LABEL_MAP.get(normalized, normalized)

def extract_category_from_context(context: str) -> Optional[str]:
    """Extract vulnerability category from context/description text."""
    if not context:
        return None
    context_lower = context.lower()
    for key, category in LABEL_MAP.items():
        if key in context_lower:
            return category
    return None

def parse_vuldeepecker_jsonl(jsonl_path: Path) -> List[Dict[str, Any]]:
    """
    Parse VulDeePecker JSONL format.
    Expected fields: id, language, code, label (or ground_truth)
    """
    snippets = []
    with open(jsonl_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                snippet = {
                    "source_id": data.get("id", f"vuldee_{line_num}"),
                    "language": data.get("language", detect_language_from_extension(data.get("file", ""))),
                    "source_code": data.get("code", data.get("source_code", "")),
                    "ground_truth_label": data.get("label", data.get("ground_truth")),
                    "ground_truth_category": data.get("category", data.get("vul_type")),
                    "source_file": data.get("file", ""),
                    "line_start": data.get("line_start", data.get("start_line")),
                    "line_end": data.get("line_end", data.get("end_line")),
                }
                snippets.append(snippet)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON at line {line_num}: {e}")
    return snippets

def parse_juliet_c_test_cases(test_dir: Path) -> List[Dict[str, Any]]:
    """
    Parse NIST Juliet C test cases.
    Structure: testdir/cwe-<id>/bad.c or good.c
    """
    snippets = []
    cwe_dirs = [d for d in test_dir.iterdir() if d.is_dir() and d.name.startswith("cwe-")]
    
    for cwe_dir in cwe_dirs:
        cwe_id = cwe_dir.name
        for test_file in cwe_dir.glob("*.c"):
            if test_file.name.startswith("bad"):
                is_vulnerable = True
                label = "vulnerable"
            elif test_file.name.startswith("good"):
                is_vulnerable = False
                label = "none"
            else:
                continue
            
            with open(test_file, 'r', encoding='utf-8', errors='ignore') as f:
                code = f.read()
            
            snippets.append({
                "source_id": str(test_file),
                "language": "C",
                "source_code": code,
                "ground_truth_label": label,
                "ground_truth_category": cwe_id.replace("cwe-", "").upper(),
                "source_file": str(test_file),
                "line_start": None,
                "line_end": None,
            })
    return snippets

def parse_juliet_java_test_cases(test_dir: Path) -> List[Dict[str, Any]]:
    """
    Parse NIST Juliet Java test cases.
    """
    snippets = []
    cwe_dirs = [d for d in test_dir.iterdir() if d.is_dir() and d.name.startswith("cwe-")]
    
    for cwe_dir in cwe_dirs:
        cwe_id = cwe_dir.name
        for test_file in cwe_dir.glob("*.java"):
            if test_file.name.startswith("bad"):
                label = "vulnerable"
            elif test_file.name.startswith("good"):
                label = "none"
            else:
                continue
            
            with open(test_file, 'r', encoding='utf-8', errors='ignore') as f:
                code = f.read()
            
            snippets.append({
                "source_id": str(test_file),
                "language": "Java",
                "source_code": code,
                "ground_truth_label": label,
                "ground_truth_category": cwe_id.replace("cwe-", "").upper(),
                "source_file": str(test_file),
                "line_start": None,
                "line_end": None,
            })
    return snippets

def parse_bigvul_directory(dir_path: Path) -> List[Dict[str, Any]]:
    """
    Parse BigVul dataset directory structure.
    Expected: directory with .c, .cpp, .js files and corresponding .json label files
    """
    snippets = []
    label_file = dir_path / "labels.json"
    
    if not label_file.exists():
        logger.warning(f"No labels.json found in {dir_path}")
        return snippets
    
    with open(label_file, 'r', encoding='utf-8') as f:
        labels = json.load(f)
    
    label_map = {item['filename']: item['label'] for item in labels}
    
    for code_file in dir_path.glob("*.[cjp]*"):
        if code_file.suffix.lower() in [".c", ".cpp", ".js", ".java"]:
            filename = code_file.name
            label = label_map.get(filename, "unknown")
            
            with open(code_file, 'r', encoding='utf-8', errors='ignore') as f:
                code = f.read()
            
            snippets.append({
                "source_id": str(code_file),
                "language": detect_language_from_extension(filename),
                "source_code": code,
                "ground_truth_label": label,
                "ground_truth_category": None,
                "source_file": str(code_file),
                "line_start": None,
                "line_end": None,
            })
    return snippets

def parse_raw_directory(raw_dir: Path) -> List[Dict[str, Any]]:
    """
    Parse raw dataset directory based on detected format.
    """
    all_snippets = []
    
    # Detect format
    if (raw_dir / "labels.json").exists():
        all_snippets.extend(parse_bigvul_directory(raw_dir))
    elif (raw_dir / "cwe-").exists() or any(d.name.startswith("cwe-") for d in raw_dir.iterdir() if d.is_dir()):
        # Check for C tests
        c_tests = list(raw_dir.glob("cwe-*/bad.c")) + list(raw_dir.glob("cwe-*/good.c"))
        if c_tests:
            all_snippets.extend(parse_juliet_c_test_cases(raw_dir))
        # Check for Java tests
        java_tests = list(raw_dir.glob("cwe-*/bad.java")) + list(raw_dir.glob("cwe-*/good.java"))
        if java_tests:
            all_snippets.extend(parse_juliet_java_test_cases(raw_dir))
    elif any(f.suffix == ".jsonl" for f in raw_dir.iterdir()):
        for jsonl_file in raw_dir.glob("*.jsonl"):
            all_snippets.extend(parse_vuldeepecker_jsonl(jsonl_file))
    else:
        # Fallback: try to parse any code files directly
        for code_file in raw_dir.glob("*.[cjp]*"):
            with open(code_file, 'r', encoding='utf-8', errors='ignore') as f:
                code = f.read()
            all_snippets.append({
                "source_id": str(code_file),
                "language": detect_language_from_extension(code_file.name),
                "source_code": code,
                "ground_truth_label": "unknown",
                "ground_truth_category": None,
                "source_file": str(code_file),
                "line_start": None,
                "line_end": None,
            })
    
    return all_snippets

def create_code_snippets(raw_data: List[Dict[str, Any]]) -> Tuple[List[CodeSnippet], List[Dict[str, Any]]]:
    """
    Convert raw parsed data to CodeSnippet entities.
    Returns: (valid_snippets, edge_cases)
    Edge cases are samples with missing ground-truth labels.
    """
    valid_snippets = []
    edge_cases = []
    
    for idx, data in enumerate(raw_data):
        snippet_id = data.get("source_id", f"snippet_{idx}")
        language = data.get("language") or detect_language_from_extension(data.get("source_file", ""))
        code = data.get("source_code", "")
        label = data.get("ground_truth_label")
        category = data.get("ground_truth_category")
        
        # Normalize label
        normalized_label = normalize_label(label)
        normalized_category = normalize_label(category) if category else None
        
        # Create CodeSnippet
        snippet = create_snippet(
            snippet_id=snippet_id,
            language=language,
            source_code=code,
            ground_truth_label=normalized_label,
            ground_truth_category=normalized_category,
            source_file=data.get("source_file"),
            line_start=data.get("line_start"),
            line_end=data.get("line_end"),
        )
        
        # Track edge cases
        if normalized_label is None:
            edge_case = {
                "snippet_id": snippet_id,
                "language": language,
                "source_file": data.get("source_file"),
                "reason": "missing_ground_truth_label",
                "original_label": label,
            }
            edge_cases.append(edge_case)
            # Include in edge case list but mark as having missing label
            snippet.label_missing = True
        
        valid_snippets.append(snippet)
    
    return valid_snippets, edge_cases

def save_snippets_to_csv(snippets: List[CodeSnippet], output_path: Path, include_missing: bool = True):
    """
    Save CodeSnippets to CSV.
    If include_missing=True, includes all snippets (with label_missing flag).
    If include_missing=False, excludes snippets with missing labels.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = [
        "snippet_id", "language", "source_code", "ground_truth_label",
        "ground_truth_category", "source_file", "line_start", "line_end",
        "label_missing"
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for snippet in snippets:
            if not include_missing and snippet.label_missing:
                continue
            
            row = {
                "snippet_id": snippet.snippet_id,
                "language": snippet.language,
                "source_code": snippet.source_code.replace('\n', '\\n').replace('\r', '\\r'),
                "ground_truth_label": snippet.ground_truth_label or "",
                "ground_truth_category": snippet.ground_truth_category or "",
                "source_file": snippet.source_file or "",
                "line_start": snippet.line_start or "",
                "line_end": snippet.line_end or "",
                "label_missing": snippet.label_missing,
            }
            writer.writerow(row)
    
    logger.info(f"Saved {len(snippets)} snippets to {output_path}")

def log_edge_cases(edge_cases: List[Dict[str, Any]], log_path: Path):
    """Log edge cases to a JSON file."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(edge_cases, f, indent=2)
    
    logger.info(f"Logged {len(edge_cases)} edge cases to {log_path}")

def main():
    """Main entry point for preprocessing pipeline."""
    project_root = get_project_root()
    raw_dir = project_root / "data" / "raw"
    processed_dir = project_root / "data" / "processed"
    
    if not raw_dir.exists():
        logger.error(f"Raw data directory not found: {raw_dir}")
        return
    
    logger.info(f"Starting preprocessing from {raw_dir}")
    
    # Parse raw data
    raw_snippets = parse_raw_directory(raw_dir)
    logger.info(f"Parsed {len(raw_snippets)} raw snippets")
    
    # Create CodeSnippet entities
    snippets, edge_cases = create_code_snippets(raw_snippets)
    logger.info(f"Created {len(snippets)} CodeSnippet entities, {len(edge_cases)} edge cases")
    
    # Save all snippets (including those with missing labels) to features.csv
    features_path = processed_dir / "features.csv"
    save_snippets_to_csv(snippets, features_path, include_missing=True)
    
    # Save only valid snippets (with labels) to predictions.csv
    predictions_path = processed_dir / "predictions.csv"
    save_snippets_to_csv(snippets, predictions_path, include_missing=False)
    
    # Log edge cases
    edge_case_log = processed_dir / "edge_cases.json"
    log_edge_cases(edge_cases, edge_case_log)
    
    logger.info("Preprocessing complete")

if __name__ == "__main__":
    main()
