"""
Preprocessing module for security vulnerability datasets.

Parses raw datasets (VulDeePecker, BigVul, NIST Juliet), extracts code snippets,
and maps them to the CodeSnippet entity. Handles edge cases for missing labels
and malformed code.
"""
import os
import json
import csv
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any, Set
import logging

from src.models.code_snippet import CodeSnippet, create_snippet
from src.utils.logger import get_logger
from src.utils.config import get_project_root

logger = get_logger(__name__)

# Constants for language detection
LANGUAGE_EXTENSIONS: Dict[str, str] = {
    '.c': 'C',
    '.cpp': 'C++',
    '.cc': 'C++',
    '.cxx': 'C++',
    '.h': 'C',
    '.hpp': 'C++',
    '.py': 'Python',
    '.js': 'JavaScript',
    '.ts': 'JavaScript',
    '.java': 'Java',
    '.go': 'Go',
    '.rb': 'Ruby',
    '.php': 'PHP',
    '.cs': 'C#',
    '.swift': 'Swift',
    '.kt': 'Kotlin',
    '.rs': 'Rust',
}

# Mapping of common vulnerability categories
CATEGORY_MAPPING: Dict[str, str] = {
    'sql': 'SQLi',
    'sql injection': 'SQLi',
    'sqli': 'SQLi',
    'xss': 'XSS',
    'cross-site scripting': 'XSS',
    'buffer overflow': 'Buffer Overflow',
    'overflow': 'Buffer Overflow',
    'bof': 'Buffer Overflow',
    'rce': 'RCE',
    'remote code execution': 'RCE',
    'command injection': 'Command Injection',
    'injection': 'Injection',
    'path traversal': 'Path Traversal',
    'directory traversal': 'Path Traversal',
    'dos': 'DoS',
    'denial of service': 'DoS',
    'memory corruption': 'Memory Corruption',
    'use after free': 'Use After Free',
    'null pointer': 'Null Pointer Dereference',
    'null pointer dereference': 'Null Pointer Dereference',
    'format string': 'Format String',
    'integer overflow': 'Integer Overflow',
    'race condition': 'Race Condition',
    'information disclosure': 'Information Disclosure',
    'privilege escalation': 'Privilege Escalation',
    'authentication': 'Authentication Bypass',
    'authorization': 'Authorization Bypass',
    'csrf': 'CSRF',
    'cross-site request forgery': 'CSRF',
    'ssrf': 'SSRF',
    'server-side request forgery': 'SSRF',
}

def detect_language_from_extension(file_path: str) -> Optional[str]:
    """Detect programming language from file extension."""
    ext = Path(file_path).suffix.lower()
    return LANGUAGE_EXTENSIONS.get(ext)

def normalize_label(label: str) -> str:
    """Normalize vulnerability labels to standard categories."""
    if not label:
        return 'unknown'
    
    label_lower = label.lower().strip()
    
    # Check for exact matches first
    if label_lower in CATEGORY_MAPPING:
        return CATEGORY_MAPPING[label_lower]
    
    # Check for partial matches
    for key, value in CATEGORY_MAPPING.items():
        if key in label_lower:
            return value
    
    # If no match found, return the original label
    return label_lower

def extract_category_from_context(context: str) -> Optional[str]:
    """Extract vulnerability category from context/description."""
    if not context:
        return None
    
    context_lower = context.lower()
    
    for key, value in CATEGORY_MAPPING.items():
        if key in context_lower:
            return value
    
    return None

def parse_vuldeepecker_jsonl(jsonl_path: Path) -> List[Dict[str, Any]]:
    """
    Parse VulDeePecker JSONL format.
    
    Expected format:
    {
        "id": "string",
        "language": "Python|C|JavaScript",
        "code": "string",
        "label": "vulnerable|safe",
        "category": "string",
        ...
    }
    """
    snippets = []
    
    if not jsonl_path.exists():
        logger.warning(f"VulDeePecker JSONL file not found: {jsonl_path}")
        return snippets
    
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            try:
                record = json.loads(line)
                
                # Extract required fields
                snippet_id = record.get('id', f'vuldeepecker_{line_num}')
                language = record.get('language') or detect_language_from_extension(snippet_id)
                code = record.get('code', '')
                label = record.get('label', '')
                category = record.get('category', '')
                
                # Normalize label and category
                normalized_label = normalize_label(label) if label else None
                normalized_category = normalize_label(category) if category else None
                
                if not normalized_category:
                    normalized_category = extract_category_from_context(record.get('description', ''))
                
                snippets.append({
                    'id': snippet_id,
                    'language': language,
                    'source_code': code,
                    'ground_truth_label': normalized_label,
                    'ground_truth_category': normalized_category,
                    'source': 'vuldeepecker',
                    'raw_record': record
                })
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error at line {line_num} in {jsonl_path}: {e}")
                continue
            except Exception as e:
                logger.error(f"Error processing line {line_num} in {jsonl_path}: {e}")
                continue
    
    logger.info(f"Parsed {len(snippets)} snippets from {jsonl_path}")
    return snippets

def parse_juliet_c_test_cases(test_dir: Path) -> List[Dict[str, Any]]:
    """
    Parse NIST Juliet C test cases.
    
    Expected structure:
    testDir/
        testcases/
            CWE123_.../
                goodG2B1.c
                goodG2B2.c
                bad.c
                ...
    """
    snippets = []
    testcases_dir = test_dir / 'testcases'
    
    if not testcases_dir.exists():
        logger.warning(f"Juliet testcases directory not found: {testcases_dir}")
        return snippets
    
    # Pattern to extract CWE ID from directory name
    cwe_pattern = re.compile(r'CWE(\d+)_')
    
    for cwe_dir in testcases_dir.iterdir():
        if not cwe_dir.is_dir():
            continue
        
        match = cwe_pattern.search(cwe_dir.name)
        cwe_id = match.group(1) if match else None
        
        if not cwe_id:
            continue
        
        # Determine vulnerability category from CWE ID
        category_map = {
            '79': 'XSS',
            '89': 'SQLi',
            '120': 'Buffer Overflow',
            '121': 'Buffer Overflow',
            '122': 'Buffer Overflow',
            '126': 'Buffer Overflow',
            '127': 'Buffer Overflow',
            '190': 'Integer Overflow',
            '416': 'Use After Free',
            '476': 'Null Pointer Dereference',
            '78': 'Command Injection',
            '22': 'Path Traversal',
            '20': 'Injection',
        }
        
        category = category_map.get(cwe_id, 'Injection')
        
        for test_file in cwe_dir.glob('*.c'):
            try:
                code = test_file.read_text(encoding='utf-8')
                
                # Determine if vulnerable based on filename
                is_vulnerable = 'bad' in test_file.name.lower() and 'good' not in test_file.name.lower()
                label = 'vulnerable' if is_vulnerable else 'safe'
                
                snippet_id = f"juliet_c_{cwe_id}_{test_file.stem}"
                
                snippets.append({
                    'id': snippet_id,
                    'language': 'C',
                    'source_code': code,
                    'ground_truth_label': label,
                    'ground_truth_category': category,
                    'source': 'juliet_c',
                    'raw_path': str(test_file)
                })
                
            except Exception as e:
                logger.error(f"Error reading {test_file}: {e}")
                continue
    
    logger.info(f"Parsed {len(snippets)} C snippets from {test_dir}")
    return snippets

def parse_juliet_java_test_cases(test_dir: Path) -> List[Dict[str, Any]]:
    """
    Parse NIST Juliet Java test cases.
    
    Expected structure:
    testDir/
        testcases/
            CWE123_.../
                GoodG2B.java
                Bad.java
                ...
    """
    snippets = []
    testcases_dir = test_dir / 'testcases'
    
    if not testcases_dir.exists():
        logger.warning(f"Juliet testcases directory not found: {testcases_dir}")
        return snippets
    
    cwe_pattern = re.compile(r'CWE(\d+)_')
    
    for cwe_dir in testcases_dir.iterdir():
        if not cwe_dir.is_dir():
            continue
        
        match = cwe_pattern.search(cwe_dir.name)
        cwe_id = match.group(1) if match else None
        
        if not cwe_id:
            continue
        
        category_map = {
            '79': 'XSS',
            '89': 'SQLi',
            '120': 'Buffer Overflow',
            '190': 'Integer Overflow',
            '78': 'Command Injection',
            '22': 'Path Traversal',
            '20': 'Injection',
        }
        
        category = category_map.get(cwe_id, 'Injection')
        
        for test_file in cwe_dir.glob('*.java'):
            try:
                code = test_file.read_text(encoding='utf-8')
                
                is_vulnerable = 'bad' in test_file.name.lower() and 'good' not in test_file.name.lower()
                label = 'vulnerable' if is_vulnerable else 'safe'
                
                snippet_id = f"juliet_java_{cwe_id}_{test_file.stem}"
                
                snippets.append({
                    'id': snippet_id,
                    'language': 'Java',
                    'source_code': code,
                    'ground_truth_label': label,
                    'ground_truth_category': category,
                    'source': 'juliet_java',
                    'raw_path': str(test_file)
                })
                
            except Exception as e:
                logger.error(f"Error reading {test_file}: {e}")
                continue
    
    logger.info(f"Parsed {len(snippets)} Java snippets from {test_dir}")
    return snippets

def parse_bigvul_directory(bigvul_dir: Path) -> List[Dict[str, Any]]:
    """
    Parse BigVul dataset directory.
    
    Expected structure:
    bigvul_dir/
        c/
            vulnerable/
            fixed/
        python/
            vulnerable/
            fixed/
        javascript/
            vulnerable/
            fixed/
    """
    snippets = []
    
    language_dirs = {
        'c': 'C',
        'python': 'Python',
        'javascript': 'JavaScript',
    }
    
    for lang_dir, language in language_dirs.items():
        lang_path = bigvul_dir / lang_dir
        
        if not lang_path.exists():
            logger.warning(f"BigVul {lang_dir} directory not found: {lang_path}")
            continue
        
        for split in ['vulnerable', 'fixed']:
            split_path = lang_path / split
            
            if not split_path.exists():
                continue
            
            label = 'vulnerable' if split == 'vulnerable' else 'safe'
            
            for file_path in split_path.iterdir():
                if not file_path.is_file():
                    continue
                
                # Skip non-code files
                if file_path.suffix.lower() not in ['.c', '.py', '.js', '.cpp', '.h', '.hpp']:
                    continue
                
                try:
                    code = file_path.read_text(encoding='utf-8')
                    detected_lang = detect_language_from_extension(str(file_path))
                    
                    # Use detected language if explicit language is missing
                    final_language = detected_lang or language
                    
                    # Try to extract category from filename or content
                    category = extract_category_from_context(file_path.name)
                    
                    snippet_id = f"bigvul_{lang_dir}_{split}_{file_path.stem}"
                    
                    snippets.append({
                        'id': snippet_id,
                        'language': final_language,
                        'source_code': code,
                        'ground_truth_label': label,
                        'ground_truth_category': category,
                        'source': 'bigvul',
                        'raw_path': str(file_path)
                    })
                    
                except Exception as e:
                    logger.error(f"Error reading {file_path}: {e}")
                    continue
    
    logger.info(f"Parsed {len(snippets)} snippets from {bigvul_dir}")
    return snippets

def parse_raw_directory(raw_dir: Path) -> List[Dict[str, Any]]:
    """
    Parse raw code snippets from a directory structure.
    
    Expected structure:
    raw_dir/
        language/
            snippet_001.c
            snippet_002.py
            ...
    """
    snippets = []
    
    if not raw_dir.exists():
        logger.warning(f"Raw directory not found: {raw_dir}")
        return snippets
    
    for lang_dir in raw_dir.iterdir():
        if not lang_dir.is_dir():
            continue
        
        language = detect_language_from_extension(str(lang_dir)) or lang_dir.name
        
        for file_path in lang_dir.iterdir():
            if not file_path.is_file():
                continue
            
            try:
                code = file_path.read_text(encoding='utf-8')
                
                snippet_id = f"raw_{lang_dir.name}_{file_path.stem}"
                
                # For raw snippets, label is unknown unless specified in metadata
                snippets.append({
                    'id': snippet_id,
                    'language': language,
                    'source_code': code,
                    'ground_truth_label': None,
                    'ground_truth_category': None,
                    'source': 'raw',
                    'raw_path': str(file_path)
                })
                
            except Exception as e:
                logger.error(f"Error reading {file_path}: {e}")
                continue
    
    logger.info(f"Parsed {len(snippets)} raw snippets from {raw_dir}")
    return snippets

def create_code_snippets(raw_data: List[Dict[str, Any]]) -> List[CodeSnippet]:
    """
    Convert raw parsed data to CodeSnippet entities.
    
    Handles edge cases:
    - Missing labels: Creates snippet with label_missing flag
    - Malformed code: Creates snippet with NaN features (will be handled in feature extraction)
    """
    snippets = []
    edge_cases = []
    
    for idx, data in enumerate(raw_data):
        snippet_id = data.get('id', f'snippet_{idx}')
        language = data.get('language', 'Unknown')
        source_code = data.get('source_code', '')
        ground_truth_label = data.get('ground_truth_label')
        ground_truth_category = data.get('ground_truth_category')
        source = data.get('source', 'unknown')
        
        # Validate code snippet
        if not source_code or not source_code.strip():
            edge_cases.append({
                'id': snippet_id,
                'issue': 'empty_code',
                'language': language,
                'source': source
            })
            # Still create snippet but mark as malformed
            snippet = create_snippet(
                id=snippet_id,
                language=language,
                source_code=source_code,
                ground_truth_label=ground_truth_label,
                ground_truth_category=ground_truth_category
            )
            snippet._malformed = True
            snippets.append(snippet)
            continue
        
        # Handle missing labels
        label_missing = ground_truth_label is None or ground_truth_label == 'unknown'
        
        try:
            snippet = create_snippet(
                id=snippet_id,
                language=language,
                source_code=source_code,
                ground_truth_label=ground_truth_label,
                ground_truth_category=ground_truth_category
            )
            snippet._label_missing = label_missing
            snippets.append(snippet)
            
            if label_missing:
                edge_cases.append({
                    'id': snippet_id,
                    'issue': 'missing_label',
                    'language': language,
                    'source': source
                })
                
        except Exception as e:
            logger.error(f"Error creating snippet {snippet_id}: {e}")
            edge_cases.append({
                'id': snippet_id,
                'issue': f'creation_error: {str(e)}',
                'language': language,
                'source': source
            })
    
    return snippets

def save_snippets_to_csv(snippets: List[CodeSnippet], output_path: Path) -> None:
    """
    Save CodeSnippet entities to CSV format.
    
    Output includes all snippets, with a flag for missing labels.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = [
        'id',
        'language',
        'source_code',
        'ground_truth_label',
        'ground_truth_category',
        'label_missing',
        'malformed'
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        
        for snippet in snippets:
            row = {
                'id': snippet.id,
                'language': snippet.language,
                'source_code': snippet.source_code,
                'ground_truth_label': snippet.ground_truth_label or '',
                'ground_truth_category': snippet.ground_truth_category or '',
                'label_missing': str(getattr(snippet, '_label_missing', False)),
                'malformed': str(getattr(snippet, '_malformed', False))
            }
            writer.writerow(row)
    
    logger.info(f"Saved {len(snippets)} snippets to {output_path}")

def log_edge_cases(edge_cases: List[Dict[str, Any]], log_path: Path) -> None:
    """Log edge cases encountered during preprocessing."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(edge_cases, f, indent=2)
    
    logger.info(f"Logged {len(edge_cases)} edge cases to {log_path}")

def main():
    """Main preprocessing pipeline entry point."""
    project_root = get_project_root()
    raw_dir = project_root / 'data' / 'raw'
    processed_dir = project_root / 'data' / 'processed'
    
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    all_snippets = []
    all_edge_cases = []
    
    # Parse VulDeePecker
    vuldeepecker_path = raw_dir / 'vuldeepecker.jsonl'
    if vuldeepecker_path.exists():
        logger.info("Parsing VulDeePecker dataset...")
        vuldeepecker_snippets = parse_vuldeepecker_jsonl(vuldeepecker_path)
        all_snippets.extend(vuldeepecker_snippets)
    
    # Parse NIST Juliet C
    juliet_c_path = raw_dir / 'juliet_c'
    if juliet_c_path.exists():
        logger.info("Parsing NIST Juliet C dataset...")
        juliet_c_snippets = parse_juliet_c_test_cases(juliet_c_path)
        all_snippets.extend(juliet_c_snippets)
    
    # Parse NIST Juliet Java
    juliet_java_path = raw_dir / 'juliet_java'
    if juliet_java_path.exists():
        logger.info("Parsing NIST Juliet Java dataset...")
        juliet_java_snippets = parse_juliet_java_test_cases(juliet_java_path)
        all_snippets.extend(juliet_java_snippets)
    
    # Parse BigVul
    bigvul_path = raw_dir / 'bigvul'
    if bigvul_path.exists():
        logger.info("Parsing BigVul dataset...")
        bigvul_snippets = parse_bigvul_directory(bigvul_path)
        all_snippets.extend(bigvul_snippets)
    
    # Parse raw directory
    raw_code_path = raw_dir / 'raw_code'
    if raw_code_path.exists():
        logger.info("Parsing raw code snippets...")
        raw_snippets = parse_raw_directory(raw_code_path)
        all_snippets.extend(raw_snippets)
    
    # Create CodeSnippet entities
    logger.info(f"Creating {len(all_snippets)} CodeSnippet entities...")
    code_snippets = create_code_snippets(all_snippets)
    
    # Save to CSV
    output_path = processed_dir / 'code_snippets.csv'
    save_snippets_to_csv(code_snippets, output_path)
    
    # Log statistics
    total = len(code_snippets)
    with_labels = sum(1 for s in code_snippets if not getattr(s, '_label_missing', False))
    missing_labels = total - with_labels
    malformed = sum(1 for s in code_snippets if getattr(s, '_malformed', False))
    
    logger.info(f"Preprocessing complete:")
    logger.info(f"  Total snippets: {total}")
    logger.info(f"  With labels: {with_labels}")
    logger.info(f"  Missing labels: {missing_labels}")
    logger.info(f"  Malformed: {malformed}")
    logger.info(f"  Output: {output_path}")

if __name__ == '__main__':
    main()
