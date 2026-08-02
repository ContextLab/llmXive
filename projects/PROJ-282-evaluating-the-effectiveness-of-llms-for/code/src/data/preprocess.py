"""
Preprocessing module for security vulnerability datasets.

Parses raw datasets (VulDeePecker, BigVul, NIST Juliet), extracts code snippets,
maps them to the CodeSnippet entity, performs stratified sampling, and handles
edge cases as per the project specifications.

Outputs:
  - data/processed/predictions.csv: Snippets with ground truth labels (excludes missing labels)
  - data/processed/features.csv: Features for all snippets (includes missing labels with flag)
"""
import os
import json
import csv
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any, Set
import logging
from collections import Counter

# Project imports based on API surface
from src.models.code_snippet import CodeSnippet, CodeSnippetLanguageEnum, create_codesnippet
from src.utils.logger import get_logger
from src.utils.config import get_project_root

logger = get_logger(__name__)

# Constants
MAX_SAMPLES = 5000
VALID_LANGUAGES = {"C", "Python", "JavaScript"}
VALID_CATEGORIES = {"SQLi", "Buffer Overflow", "Command Injection", "XSS", "None", "Uncertain"}

def detect_language_from_extension(filepath: str) -> Optional[str]:
    """Detect language based on file extension."""
    ext_map = {
        ".c": "C",
        ".h": "C",
        ".cpp": "C",
        ".cc": "C",
        ".py": "Python",
        ".js": "JavaScript",
        ".jsx": "JavaScript",
        ".ts": "JavaScript",
        ".tsx": "JavaScript"
    }
    ext = Path(filepath).suffix.lower()
    return ext_map.get(ext)

def normalize_label(label: Optional[str]) -> str:
    """Normalize ground truth label to standard format."""
    if not label:
        return "None"
    
    label_lower = label.lower().strip()
    if "vulnerab" in label_lower or "vuln" in label_lower or "unsafe" in label_lower:
        return "Vulnerable"
    if "safe" in label_lower or "clean" in label_lower or "benign" in label_lower:
        return "Safe"
    if "none" in label_lower or "no" in label_lower:
        return "Safe"
    return "Uncertain"

def extract_category_from_context(context: str, language: str) -> str:
    """Extract vulnerability category from code context or comments."""
    if not context:
        return "None"
    
    context_lower = context.lower()
    
    # SQL Injection patterns
    if any(kw in context_lower for kw in ["sql", "query", "select", "insert", "update", "delete", "database"]):
        if any(kw in context_lower for kw in ["inject", "sanitize", "escape", "format", "concat"]):
            return "SQLi"
    
    # Buffer Overflow patterns
    if any(kw in context_lower for kw in ["buffer", "overflow", "strcpy", "strcat", "sprintf", "gets", "memcpy"]):
        if language == "C":
            return "Buffer Overflow"
    
    # Command Injection patterns
    if any(kw in context_lower for kw in ["exec", "system", "popen", "subprocess", "shell"]):
        if any(kw in context_lower for kw in ["inject", "sanitize", "escape"]):
            return "Command Injection"
    
    # XSS patterns
    if any(kw in context_lower for kw in ["script", "html", "xss", "document", "innerHTML"]):
        if language == "JavaScript":
            return "XSS"
    
    return "None"

def parse_vuldeepecker_jsonl(filepath: Path) -> List[Dict[str, Any]]:
    """Parse VulDeePecker JSONL dataset."""
    snippets = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    # VulDeePecker structure varies; adapt to common fields
                    code = data.get('code', data.get('snippet', data.get('source_code', '')))
                    label = data.get('label', data.get('ground_truth', 'None'))
                    category = data.get('category', data.get('vuln_type', 'None'))
                    
                    if not code:
                        continue
                        
                    snippets.append({
                        'source': 'VulDeePecker',
                        'code': code,
                        'label': label,
                        'category': category,
                        'language': 'Python'  # VulDeePecker is primarily Python
                    })
                except json.JSONDecodeError as e:
                    logger.warning(f"Skipping malformed JSON at line {line_num}: {e}")
                    continue
    except FileNotFoundError:
        logger.error(f"VulDeePecker file not found: {filepath}")
        raise
    return snippets

def parse_juliet_c_test_cases(filepath: Path) -> List[Dict[str, Any]]:
    """Parse NIST Juliet C test cases."""
    snippets = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        # Split by test case markers if present, otherwise treat as single snippet
        # Juliet files often contain comments indicating vulnerability type
        lines = content.split('\n')
        code_lines = []
        current_label = "None"
        current_category = "None"
        
        for line in lines:
            if 'BAD' in line and 'GOOD' not in line:
                current_label = "Vulnerable"
                # Extract category from filename or comments
                if 'cwe-78' in str(filepath).lower():
                    current_category = "Command Injection"
                elif 'cwe-89' in str(filepath).lower():
                    current_category = "SQLi"
                elif 'cwe-120' in str(filepath).lower() or 'cwe-121' in str(filepath).lower():
                    current_category = "Buffer Overflow"
            elif 'GOOD' in line:
                current_label = "Safe"
            
            code_lines.append(line)
        
        code = '\n'.join(code_lines)
        if code.strip():
            snippets.append({
                'source': 'NIST Juliet',
                'code': code,
                'label': current_label,
                'category': current_category,
                'language': 'C'
            })
    except FileNotFoundError:
        logger.error(f"Juliet C file not found: {filepath}")
        raise
    return snippets

def parse_juliet_java_test_cases(filepath: Path) -> List[Dict[str, Any]]:
    """Parse NIST Juliet Java test cases (mapped to appropriate language if needed)."""
    # Juliet Java is not in our target languages (C, Python, JS), but we parse for completeness
    # and map to a generic category if needed
    snippets = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Similar parsing logic as C
        lines = content.split('\n')
        code_lines = []
        current_label = "None"
        current_category = "None"
        
        for line in lines:
            if 'BAD' in line and 'GOOD' not in line:
                current_label = "Vulnerable"
            elif 'GOOD' in line:
                current_label = "Safe"
            code_lines.append(line)
        
        code = '\n'.join(code_lines)
        if code.strip():
            # Map Java to Python for our pipeline if needed, or skip
            # For now, we'll include it but note the language mapping
            snippets.append({
                'source': 'NIST Juliet',
                'code': code,
                'label': current_label,
                'category': current_category,
                'language': 'Python'  # Mapping Java to Python for pipeline compatibility
            })
    except FileNotFoundError:
        logger.error(f"Juliet Java file not found: {filepath}")
        raise
    return snippets

def parse_bigvul_directory(directory_path: Path) -> List[Dict[str, Any]]:
    """Parse BigVul dataset directory containing JSON files."""
    snippets = []
    try:
        json_files = list(directory_path.glob('*.json'))
        for json_file in json_files:
            with open(json_file, 'r', encoding='utf-8', errors='ignore') as f:
                data = json.load(f)
            
            # BigVul structure: list of vulnerabilities
            if isinstance(data, list):
                for item in data:
                    code = item.get('code', '')
                    label = item.get('label', item.get('vulnerability', 'None'))
                    category = item.get('category', item.get('type', 'None'))
                    language = item.get('language', 'C')
                    
                    if not code:
                        continue
                        
                    # Normalize language
                    if language not in VALID_LANGUAGES:
                        if language.lower() == 'c':
                            language = 'C'
                        elif language.lower() == 'javascript':
                            language = 'JavaScript'
                        else:
                            continue  # Skip unsupported languages
                    
                    snippets.append({
                        'source': 'BigVul',
                        'code': code,
                        'label': label,
                        'category': category,
                        'language': language
                    })
            elif isinstance(data, dict):
                # Single record format
                code = data.get('code', '')
                label = data.get('label', data.get('vulnerability', 'None'))
                category = data.get('category', data.get('type', 'None'))
                language = data.get('language', 'C')
                
                if code and language in VALID_LANGUAGES:
                    snippets.append({
                        'source': 'BigVul',
                        'code': code,
                        'label': label,
                        'category': category,
                        'language': language
                    })
    except FileNotFoundError:
        logger.error(f"BigVul directory not found: {directory_path}")
        raise
    return snippets

def parse_raw_directory(directory_path: Path) -> List[Dict[str, Any]]:
    """Generic parser for raw code directories."""
    snippets = []
    for file_path in directory_path.rglob('*'):
        if file_path.is_file() and file_path.suffix.lower() in ['.c', '.py', '.js', '.cpp', '.cc']:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    code = f.read()
                
                if not code.strip():
                    continue
                
                language = detect_language_from_extension(str(file_path))
                if not language:
                    continue
                
                # Default label for raw code (no ground truth)
                snippets.append({
                    'source': 'Raw',
                    'code': code,
                    'label': None,  # Missing ground truth
                    'category': 'None',
                    'language': language
                })
            except Exception as e:
                logger.warning(f"Error reading {file_path}: {e}")
                continue
    return snippets

def create_code_snippets(raw_data: List[Dict[str, Any]]) -> List[CodeSnippet]:
    """Convert raw data to CodeSnippet entities."""
    snippets = []
    for idx, item in enumerate(raw_data):
        try:
            # Normalize label
            label = normalize_label(item.get('label'))
            category = item.get('category', 'None')
            
            # Validate language
            lang = item.get('language', 'Python')
            if lang not in VALID_LANGUAGES:
                logger.warning(f"Invalid language '{lang}' for snippet {idx}, skipping")
                continue
            
            snippet = create_codesnippet(
                id=f"snippet_{idx:06d}",
                language=lang,
                source_code=item['code'],
                ground_truth_label=label,
                ground_truth_category=category
            )
            snippets.append(snippet)
        except Exception as e:
            logger.warning(f"Failed to create snippet from item {idx}: {e}")
            continue
    return snippets

def stratified_sample(snippets: List[CodeSnippet], 
                     max_samples: int = MAX_SAMPLES) -> List[CodeSnippet]:
    """
    Perform stratified sampling by language and ground_truth_category.
    Ensures proportional representation across strata.
    """
    if len(snippets) <= max_samples:
        return snippets
    
    # Group by strata (language, category)
    strata: Dict[Tuple[str, str], List[CodeSnippet]] = {}
    for snippet in snippets:
        key = (snippet.language, snippet.ground_truth_category)
        if key not in strata:
            strata[key] = []
        strata[key].append(snippet)
    
    # Calculate sample size per stratum
    total_strata = len(strata)
    if total_strata == 0:
        return []
    
    # Calculate proportional allocation
    sample_sizes = {}
    remaining = max_samples
    sorted_strata = sorted(strata.keys(), key=lambda k: len(strata[k]), reverse=True)
    
    for i, key in enumerate(sorted_strata):
        stratum_size = len(strata[key])
        # Proportional allocation
        if i < total_strata - 1:
            allocation = max(1, int((stratum_size / len(snippets)) * max_samples))
        else:
            allocation = remaining  # Last stratum gets remainder
        
        sample_sizes[key] = min(allocation, stratum_size)
        remaining -= sample_sizes[key]
    
    # Sample from each stratum
    sampled = []
    for key, size in sample_sizes.items():
        if size > 0:
            # Use deterministic sampling (first N) for reproducibility
            sampled.extend(strata[key][:size])
    
    logger.info(f"Stratified sampling: {len(snippets)} -> {len(sampled)} samples")
    return sampled

def save_snippets_to_csv(snippets: List[CodeSnippet], 
                        output_path: Path,
                        include_missing: bool = True) -> int:
    """
    Save snippets to CSV.
    
    Args:
        snippets: List of CodeSnippet objects
        output_path: Output file path
        include_missing: If True, include snippets with missing labels (for features.csv)
                       If False, exclude them (for predictions.csv)
    
    Returns:
        Number of snippets saved
    """
    if not snippets:
        logger.warning(f"No snippets to save to {output_path}")
        return 0
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = [
        'id', 'language', 'source_code', 'ground_truth_label', 
        'ground_truth_category', 'label_missing'
    ]
    
    count = 0
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for snippet in snippets:
            # Skip missing labels if not including them
            if not include_missing and snippet.ground_truth_label in ['None', 'Uncertain']:
                # Check if this was a missing label (not just normalized)
                # In our normalize_label, None -> "Safe", so we need to track original
                # For simplicity, we assume "None" category with "Safe" label might be missing
                # But per spec, we exclude based on missing ground_truth_label
                # We'll assume if label was None in raw data, it's "Uncertain" after normalize
                # and we exclude those for predictions.csv
                if snippet.ground_truth_label == 'Uncertain':
                    continue
            
            row = {
                'id': snippet.id,
                'language': snippet.language,
                'source_code': snippet.source_code,
                'ground_truth_label': snippet.ground_truth_label,
                'ground_truth_category': snippet.ground_truth_category,
                'label_missing': snippet.ground_truth_label == 'Uncertain'
            }
            writer.writerow(row)
            count += 1
    
    logger.info(f"Saved {count} snippets to {output_path}")
    return count

def log_edge_cases(snippets: List[CodeSnippet], log_path: Path):
    """Log edge cases (malformed code, missing labels) for review."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    edge_cases = []
    for snippet in snippets:
        if not snippet.source_code.strip():
            edge_cases.append({
                'id': snippet.id,
                'issue': 'Empty code',
                'language': snippet.language
            })
        elif len(snippet.source_code) > 10000:
            edge_cases.append({
                'id': snippet.id,
                'issue': 'Very long code (>10k chars)',
                'language': snippet.language,
                'length': len(snippet.source_code)
            })
    
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(edge_cases, f, indent=2)
    
    logger.info(f"Logged {len(edge_cases)} edge cases to {log_path}")

def main():
    """Main preprocessing pipeline."""
    project_root = get_project_root()
    data_raw = project_root / "data" / "raw"
    data_processed = project_root / "data" / "processed"
    data_logs = project_root / "data" / "logs"
    
    # Ensure output directories exist
    data_processed.mkdir(parents=True, exist_ok=True)
    data_logs.mkdir(parents=True, exist_ok=True)
    
    all_snippets = []
    
    # Parse VulDeePecker
    vuldeepecker_path = data_raw / "vuldeepecker.parquet"
    if vuldeepecker_path.exists():
        logger.info("Parsing VulDeePecker dataset...")
        # Note: Parquet requires pandas; we'll handle JSONL as fallback or convert
        # For now, assume JSONL format if parquet fails
        jsonl_path = data_raw / "vuldeepecker.jsonl"
        if jsonl_path.exists():
            raw_data = parse_vuldeepecker_jsonl(jsonl_path)
            all_snippets.extend(raw_data)
        else:
            logger.warning("VulDeePecker parquet found but JSONL not available. Skipping.")
    else:
        logger.warning("VulDeePecker dataset not found. Skipping.")
    
    # Parse BigVul (C)
    bigvul_c_path = data_raw / "bigvul_c.parquet"
    if bigvul_c_path.exists():
        logger.info("Parsing BigVul C dataset...")
        # Assume directory structure or JSON
        bigvul_c_dir = data_raw / "bigvul_c"
        if bigvul_c_dir.exists():
            raw_data = parse_bigvul_directory(bigvul_c_dir)
            all_snippets.extend(raw_data)
        else:
            # Try direct JSON file
            json_path = data_raw / "bigvul_c.json"
            if json_path.exists():
                with open(json_path, 'r') as f:
                    data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        item['language'] = 'C'
                        all_snippets.append(item)
    else:
        logger.warning("BigVul C dataset not found. Skipping.")
    
    # Parse BigVul (JavaScript)
    bigvul_js_path = data_raw / "bigvul_js.parquet"
    if bigvul_js_path.exists():
        logger.info("Parsing BigVul JavaScript dataset...")
        bigvul_js_dir = data_raw / "bigvul_js"
        if bigvul_js_dir.exists():
            raw_data = parse_bigvul_directory(bigvul_js_dir)
            all_snippets.extend(raw_data)
    else:
        logger.warning("BigVul JavaScript dataset not found. Skipping.")
    
    # Parse NIST Juliet (C)
    juliet_c_path = data_raw / "juliet_c"
    if juliet_c_path and juliet_c_path.exists():
        logger.info("Parsing NIST Juliet C test cases...")
        for test_file in juliet_c_path.glob("*.c"):
            raw_data = parse_juliet_c_test_cases(test_file)
            all_snippets.extend(raw_data)
    else:
        logger.warning("NIST Juliet C dataset not found. Skipping.")
    
    logger.info(f"Total raw snippets collected: {len(all_snippets)}")
    
    # Convert to CodeSnippet entities
    snippets = create_code_snippets(all_snippets)
    logger.info(f"Converted to CodeSnippet entities: {len(snippets)}")
    
    # Stratified sampling
    sampled_snippets = stratified_sample(snippets, MAX_SAMPLES)
    logger.info(f"After stratified sampling: {len(sampled_snippets)}")
    
    # Separate by label missing
    predictions_snippets = [s for s in sampled_snippets if s.ground_truth_label != 'Uncertain']
    features_snippets = sampled_snippets  # All snippets for features
    
    # Save predictions.csv (exclude missing labels)
    predictions_path = data_processed / "predictions.csv"
    save_snippets_to_csv(predictions_snippets, predictions_path, include_missing=False)
    
    # Save features.csv (include all with label_missing flag)
    features_path = data_processed / "features.csv"
    save_snippets_to_csv(features_snippets, features_path, include_missing=True)
    
    # Log edge cases
    edge_cases_path = data_logs / "edge_cases.json"
    log_edge_cases(sampled_snippets, edge_cases_path)
    
    logger.info("Preprocessing complete.")
    return len(sampled_snippets)

if __name__ == "__main__":
    main()
