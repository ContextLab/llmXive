import os
import json
import csv
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime

from src.models.code_snippet import CodeSnippet, create_snippet
from src.utils.logger import get_logger, log_stage_start, log_stage_complete, log_stage_failure

logger = get_logger(__name__)

# Constants for raw data directories (matching T011 download paths)
RAW_DATA_DIR = Path("data/raw")
PROCESSED_DATA_DIR = Path("data/processed")

# Mapping for VulDeePecker JSONL structure
VULDEEPCKER_FIELDS = {
    "id": "id",
    "code": "code",
    "label": "label",
    "language": "language",
    "category": "category",
    "context": "context"
}

def detect_language_from_extension(file_path: str) -> str:
    """Detect programming language based on file extension."""
    ext_map = {
        ".py": "python",
        ".c": "c",
        ".cpp": "cpp",
        ".java": "java",
        ".js": "javascript",
        ".ts": "typescript",
        ".go": "go",
        ".rs": "rust",
        ".rb": "ruby",
        ".php": "php",
    }
    ext = Path(file_path).suffix.lower()
    return ext_map.get(ext, "unknown")

def normalize_label(label: Any) -> str:
    """Normalize vulnerability labels to standard format."""
    if label is None:
        return "unknown"
    
    label_str = str(label).lower().strip()
    
    # Map common variations
    if label_str in ["vulnerable", "vuln", "1", "true", "yes", "positive"]:
        return "vulnerable"
    elif label_str in ["safe", "non-vulnerable", "0", "false", "no", "negative", "benign"]:
        return "safe"
    elif label_str in ["unknown", "unlabeled", "null", ""]:
        return "unknown"
    else:
        return label_str

def extract_category_from_context(context: Optional[str]) -> str:
    """Extract vulnerability category from context or code comments."""
    if not context:
        return "unknown"
    
    context_lower = context.lower()
    
    # Common vulnerability categories
    categories = [
        ("sql", "sql_injection"),
        ("command", "command_injection"),
        ("xss", "xss"),
        ("buffer overflow", "buffer_overflow"),
        ("overflow", "overflow"),
        ("path traversal", "path_traversal"),
        ("directory traversal", "path_traversal"),
        ("ldap", "ldap_injection"),
        ("xpath", "xpath_injection"),
        ("xxe", "xxe"),
        ("csrf", "csrf"),
        ("ssrf", "ssrf"),
        ("race", "race_condition"),
        ("memory", "memory_corruption"),
        ("integer", "integer_overflow"),
        ("format", "format_string"),
        ("unvalidated", "input_validation"),
        ("input", "input_validation"),
    ]
    
    for keyword, category in categories:
        if keyword in context_lower:
            return category
    
    return "unknown"

def parse_vuldeepecker_jsonl(jsonl_path: Path) -> List[Dict[str, Any]]:
    """Parse VulDeePecker JSONL dataset file."""
    snippets = []
    
    if not jsonl_path.exists():
        logger.warning(f"VulDeePecker file not found: {jsonl_path}")
        return snippets
    
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            try:
                record = json.loads(line)
                
                # Extract fields with fallbacks
                snippet_id = record.get("id", f"vuldeepecker_{line_num}")
                code = record.get("code", "")
                label = record.get("label", "unknown")
                language = record.get("language", detect_language_from_extension(snippet_id))
                category = record.get("category", extract_category_from_context(record.get("context", "")))
                context = record.get("context", "")
                
                # Skip if essential fields are missing
                if not code or not code.strip():
                    logger.debug(f"Skipping line {line_num}: empty code")
                    continue
                
                snippets.append({
                    "id": snippet_id,
                    "code": code,
                    "label": label,
                    "language": language,
                    "category": category,
                    "source": "vuldeepecker",
                    "context": context
                })
                
            except json.JSONDecodeError as e:
                logger.warning(f"Skipping malformed JSON at line {line_num}: {e}")
                continue
            except Exception as e:
                logger.warning(f"Error parsing line {line_num}: {e}")
                continue
    
    logger.info(f"Parsed {len(snippets)} snippets from {jsonl_path}")
    return snippets

def parse_juliet_c_test_cases(juliet_dir: Path) -> List[Dict[str, Any]]:
    """Parse Juliet C test case directory structure."""
    snippets = []
    
    if not juliet_dir.exists():
        logger.warning(f"Juliet C directory not found: {juliet_dir}")
        return snippets
    
    # Juliet structure: c/{test_case}/{variant}/...
    for test_case_dir in juliet_dir.iterdir():
        if not test_case_dir.is_dir():
            continue
        
        test_case_name = test_case_dir.name
        
        for variant_dir in test_case_dir.iterdir():
            if not variant_dir.is_dir():
                continue
            
            variant_name = variant_dir.name
            
            # Check for 'good' or 'bad' in variant name
            is_vulnerable = "bad" in variant_name.lower()
            label = "vulnerable" if is_vulnerable else "safe"
            
            # Find source files
            for src_file in variant_dir.rglob("*.c"):
                try:
                    with open(src_file, 'r', encoding='utf-8', errors='ignore') as f:
                        code = f.read()
                    
                    if not code.strip():
                        continue
                    
                    snippet_id = f"juliet_c_{test_case_name}_{variant_name}_{src_file.stem}"
                    category = extract_category_from_context(test_case_name)
                    
                    snippets.append({
                        "id": snippet_id,
                        "code": code,
                        "label": label,
                        "language": "c",
                        "category": category,
                        "source": "juliet_c",
                        "context": test_case_name
                    })
                except Exception as e:
                    logger.warning(f"Error reading {src_file}: {e}")
                    continue
    
    logger.info(f"Parsed {len(snippets)} C snippets from {juliet_dir}")
    return snippets

def parse_juliet_java_test_cases(juliet_dir: Path) -> List[Dict[str, Any]]:
    """Parse Juliet Java test case directory structure."""
    snippets = []
    
    if not juliet_dir.exists():
        logger.warning(f"Juliet Java directory not found: {juliet_dir}")
        return snippets
    
    # Juliet structure: java/{test_case}/{variant}/...
    for test_case_dir in juliet_dir.iterdir():
        if not test_case_dir.is_dir():
            continue
        
        test_case_name = test_case_dir.name
        
        for variant_dir in test_case_dir.iterdir():
            if not variant_dir.is_dir():
                continue
            
            variant_name = variant_dir.name
            
            # Check for 'good' or 'bad' in variant name
            is_vulnerable = "bad" in variant_name.lower()
            label = "vulnerable" if is_vulnerable else "safe"
            
            # Find source files
            for src_file in variant_dir.rglob("*.java"):
                try:
                    with open(src_file, 'r', encoding='utf-8', errors='ignore') as f:
                        code = f.read()
                    
                    if not code.strip():
                        continue
                    
                    snippet_id = f"juliet_java_{test_case_name}_{variant_name}_{src_file.stem}"
                    category = extract_category_from_context(test_case_name)
                    
                    snippets.append({
                        "id": snippet_id,
                        "code": code,
                        "label": label,
                        "language": "java",
                        "category": category,
                        "source": "juliet_java",
                        "context": test_case_name
                    })
                except Exception as e:
                    logger.warning(f"Error reading {src_file}: {e}")
                    continue
    
    logger.info(f"Parsed {len(snippets)} Java snippets from {juliet_dir}")
    return snippets

def parse_raw_directory(raw_dir: Path) -> List[Dict[str, Any]]:
    """Parse all raw dataset files in the data/raw directory."""
    all_snippets = []
    
    if not raw_dir.exists():
        logger.error(f"Raw data directory not found: {raw_dir}")
        return all_snippets
    
    # Parse VulDeePecker JSONL files
    for jsonl_file in raw_dir.glob("*.jsonl"):
        if "vuldeepecker" in jsonl_file.name.lower():
            all_snippets.extend(parse_vuldeepecker_jsonl(jsonl_file))
    
    # Parse Juliet C test cases
    juliet_c_dir = raw_dir / "juliet" / "c"
    if juliet_c_dir.exists():
        all_snippets.extend(parse_juliet_c_test_cases(juliet_c_dir))
    
    # Parse Juliet Java test cases
    juliet_java_dir = raw_dir / "juliet" / "java"
    if juliet_java_dir.exists():
        all_snippets.extend(parse_juliet_java_test_cases(juliet_java_dir))
    
    logger.info(f"Total snippets parsed: {len(all_snippets)}")
    return all_snippets

def create_code_snippets(raw_snippets: List[Dict[str, Any]]) -> List[CodeSnippet]:
    """Convert raw parsed snippets to CodeSnippet entities."""
    code_snippets = []
    excluded_count = 0
    
    for raw in raw_snippets:
        # Normalize label
        normalized_label = normalize_label(raw.get("label"))
        
        # Skip samples with missing or unknown labels
        if normalized_label == "unknown":
            excluded_count += 1
            logger.debug(f"Excluded snippet {raw.get('id')}: unknown label")
            continue
        
        # Create CodeSnippet entity
        snippet = create_snippet(
            snippet_id=raw.get("id", ""),
            language=raw.get("language", "unknown"),
            source_code=raw.get("code", ""),
            ground_truth_label=normalized_label,
            ground_truth_category=raw.get("category", "unknown")
        )
        
        code_snippets.append(snippet)
    
    logger.info(f"Created {len(code_snippets)} CodeSnippet entities, excluded {excluded_count} with missing labels")
    return code_snippets

def save_snippets_to_csv(snippets: List[CodeSnippet], output_path: Path) -> None:
    """Save CodeSnippet entities to a CSV file."""
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Write header
        writer.writerow([
            "id",
            "language",
            "source_code",
            "ground_truth_label",
            "ground_truth_category",
            "created_at"
        ])
        
        # Write data
        for snippet in snippets:
            writer.writerow([
                snippet.id,
                snippet.language,
                snippet.source_code.replace('\n', '\\n'),  # Escape newlines for CSV
                snippet.ground_truth_label,
                snippet.ground_truth_category,
                datetime.now().isoformat()
            ])
    
    logger.info(f"Saved {len(snippets)} snippets to {output_path}")

def main():
    """Main entry point for preprocessing pipeline."""
    log_stage_start("preprocess", "Parsing raw datasets and creating CodeSnippet entities")
    
    try:
        # Parse all raw datasets
        raw_snippets = parse_raw_directory(RAW_DATA_DIR)
        
        if not raw_snippets:
            log_stage_failure("preprocess", "No snippets found in raw data directory")
            return
        
        # Create CodeSnippet entities (excludes unknown labels)
        code_snippets = create_code_snippets(raw_snippets)
        
        if not code_snippets:
            log_stage_failure("preprocess", "No valid snippets after filtering unknown labels")
            return
        
        # Save to CSV
        output_path = PROCESSED_DATA_DIR / "snippets.csv"
        save_snippets_to_csv(code_snippets, output_path)
        
        log_stage_complete("preprocess", f"Successfully processed {len(code_snippets)} snippets")
        
    except Exception as e:
        log_stage_failure("preprocess", f"Preprocessing failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
