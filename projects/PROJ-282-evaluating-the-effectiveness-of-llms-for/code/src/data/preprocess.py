import os
import json
import csv
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from src.models.code_snippet import CodeSnippet, create_snippet
from src.utils.logger import get_logger, log_stage_start, log_stage_complete, log_stage_failure

logger = get_logger(__name__)

# Mapping for language detection based on file extension
EXTENSION_TO_LANGUAGE = {
    '.py': 'Python',
    '.c': 'C',
    '.cpp': 'C++',
    '.cc': 'C++',
    '.cxx': 'C++',
    '.java': 'Java',
    '.js': 'JavaScript',
    '.ts': 'TypeScript',
    '.go': 'Go',
    '.rb': 'Ruby',
    '.php': 'PHP',
    '.cs': 'C#',
    '.swift': 'Swift',
    '.kt': 'Kotlin',
    '.rs': 'Rust',
}

# Mapping for label normalization
LABEL_NORMALIZATION_MAP = {
    'vulnerable': 'vulnerable',
    'vuln': 'vulnerable',
    'unsafe': 'vulnerable',
    'bad': 'vulnerable',
    'insecure': 'vulnerable',
    'secure': 'safe',
    'safe': 'safe',
    'benign': 'safe',
    'clean': 'safe',
    'ok': 'safe',
    'normal': 'safe',
    '1': 'vulnerable',
    '0': 'safe',
    'true': 'vulnerable',
    'false': 'safe',
    'yes': 'vulnerable',
    'no': 'safe',
}

# Vulnerability category patterns
VULNERABILITY_CATEGORIES = {
    'sql_injection': [r'sql\s*injection', r'sqli', r'database\s*injection'],
    'buffer_overflow': [r'buffer\s*overflow', r'overflow', r'heap\s*overflow', r'stack\s*overflow'],
    'code_injection': [r'code\s*injection', r'command\s*injection', r'os\s*command'],
    'xss': [r'cross\s*sit.*script', r'xss', r'script\s*injection'],
    'path_injection': [r'path\s*traversal', r'directory\s*traversal', r'path\s*injection'],
    'command_injection': [r'command\s*injection', r'os\s*command\s*injection'],
    'authentication': [r'auth\s*bypass', r'authentication\s*bypass', r'login\s*bypass'],
    'authorization': [r'privilege\s*escalation', r'authorization\s*bypass', r'access\s*control'],
    'information_disclosure': [r'information\s*disclosure', r'data\s*leak', r'sensitive\s*data'],
    'crypto': [r'weak\s*crypto', r'broken\s*crypto', r'crypto\s*failure'],
    'dos': [r'denial\s*of\s*service', r'dos', r'distributed\s*denial'],
    'memory_corruption': [r'memory\s*corruption', r'use\s*after\s*free', r'double\s*free'],
    'race_condition': [r'race\s*condition', r'time\s*of\s*check\s*time\s*of\s*use', r'toctou'],
    'other': [r'vulnerability', r'security\s*issue', r'security\s*bug'],
}

def detect_language_from_extension(file_path: str) -> Optional[str]:
    """Detect programming language from file extension."""
    ext = Path(file_path).suffix.lower()
    return EXTENSION_TO_LANGUAGE.get(ext)

def normalize_label(label: Any) -> Optional[str]:
    """Normalize vulnerability label to 'vulnerable' or 'safe'."""
    if label is None:
        return None
    
    label_str = str(label).strip().lower()
    if not label_str:
        return None
    
    # Check direct mapping
    if label_str in LABEL_NORMALIZATION_MAP:
        return LABEL_NORMALIZATION_MAP[label_str]
    
    # Check if it's already a valid label
    if label_str in ['vulnerable', 'safe']:
        return label_str
    
    return None

def extract_category_from_context(code: str, context: Optional[str] = None) -> Optional[str]:
    """Extract vulnerability category from code or context."""
    text_to_search = f"{code} {context or ''}".lower()
    
    for category, patterns in VULNERABILITY_CATEGORIES.items():
        for pattern in patterns:
            if re.search(pattern, text_to_search):
                return category
    
    return None

def parse_vuldeepecker_jsonl(jsonl_path: Path) -> List[Dict[str, Any]]:
    """Parse VulDeePecker JSONL dataset."""
    snippets = []
    
    if not jsonl_path.exists():
        logger.error(f"VulDeePecker file not found: {jsonl_path}")
        return snippets
    
    with open(jsonl_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            try:
                record = json.loads(line)
                
                # Extract code snippet
                code = record.get('code', '')
                if not code:
                    continue
                
                # Extract label
                label = record.get('label')
                normalized_label = normalize_label(label)
                
                # Extract language (VulDeePecker is primarily Python)
                language = record.get('language', 'Python')
                if language not in ['Python', 'C', 'Java', 'JavaScript']:
                    language = detect_language_from_extension(record.get('file', '')) or 'Python'
                
                # Extract context/metadata
                context = record.get('context', '')
                file_path = record.get('file', '')
                
                snippets.append({
                    'code': code,
                    'label': normalized_label,
                    'language': language,
                    'context': context,
                    'file_path': file_path,
                    'source': 'VulDeePecker',
                    'line_number': line_num,
                })
                
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON at line {line_num}: {e}")
                continue
            except Exception as e:
                logger.warning(f"Error processing line {line_num}: {e}")
                continue
    
    return snippets

def parse_juliet_c_test_cases(directory: Path) -> List[Dict[str, Any]]:
    """Parse Juliet C test cases."""
    snippets = []
    
    if not directory.exists():
        logger.error(f"Juliet C directory not found: {directory}")
        return snippets
    
    # Walk through directory structure
    for root, _, files in os.walk(directory):
        for file in files:
            if not file.endswith('.c'):
                continue
            
            file_path = Path(root) / file
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Determine vulnerability status from filename
                # Juliet uses naming convention: 123456_01.c (vulnerable) vs 123456_01_bad.c
                # Actually, Juliet uses: *_good.c (safe) and *_bad.c (vulnerable)
                is_vulnerable = '_bad.c' in str(file_path)
                is_safe = '_good.c' in str(file_path)
                
                if is_vulnerable:
                    label = 'vulnerable'
                elif is_safe:
                    label = 'safe'
                else:
                    # Try to infer from content
                    label = None
                
                # Extract category from filename
                # Format: CWE_ID_testcase.c
                match = re.search(r'CWE(\d+)', str(file_path))
                if match:
                    cwe_id = match.group(1)
                    # Map CWE to category (simplified)
                    category = extract_category_from_context("", f"CWE-{cwe_id}")
                else:
                    category = None
                
                snippets.append({
                    'code': content,
                    'label': label,
                    'language': 'C',
                    'context': str(file_path),
                    'file_path': str(file_path),
                    'source': 'Juliet_C',
                    'cwe_id': match.group(1) if match else None,
                })
                
            except Exception as e:
                logger.warning(f"Error processing {file_path}: {e}")
                continue
    
    return snippets

def parse_juliet_java_test_cases(directory: Path) -> List[Dict[str, Any]]:
    """Parse Juliet Java test cases."""
    snippets = []
    
    if not directory.exists():
        logger.error(f"Juliet Java directory not found: {directory}")
        return snippets
    
    for root, _, files in os.walk(directory):
        for file in files:
            if not file.endswith('.java'):
                continue
            
            file_path = Path(root) / file
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Determine vulnerability status
                is_vulnerable = '_bad' in str(file_path)
                is_safe = '_good' in str(file_path)
                
                if is_vulnerable:
                    label = 'vulnerable'
                elif is_safe:
                    label = 'safe'
                else:
                    label = None
                
                # Extract category from filename
                match = re.search(r'CWE(\d+)', str(file_path))
                if match:
                    cwe_id = match.group(1)
                    category = extract_category_from_context("", f"CWE-{cwe_id}")
                else:
                    category = None
                
                snippets.append({
                    'code': content,
                    'label': label,
                    'language': 'Java',
                    'context': str(file_path),
                    'file_path': str(file_path),
                    'source': 'Juliet_Java',
                    'cwe_id': match.group(1) if match else None,
                })
                
            except Exception as e:
                logger.warning(f"Error processing {file_path}: {e}")
                continue
    
    return snippets

def parse_raw_directory(directory: Path, language: str) -> List[Dict[str, Any]]:
    """Parse raw code directory for a specific language."""
    snippets = []
    language_extensions = {ext for ext, lang in EXTENSION_TO_LANGUAGE.items() if lang == language}
    
    if not directory.exists():
        logger.error(f"Raw directory not found: {directory}")
        return snippets
    
    for root, _, files in os.walk(directory):
        for file in files:
            ext = Path(file).suffix.lower()
            if ext not in language_extensions:
                continue
            
            file_path = Path(root) / file
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    code = f.read()
                
                # For raw directories, we don't have ground truth labels
                # Mark as None (will be excluded from accuracy calculations)
                snippets.append({
                    'code': code,
                    'label': None,
                    'language': language,
                    'context': str(file_path),
                    'file_path': str(file_path),
                    'source': 'raw',
                })
                
            except Exception as e:
                logger.warning(f"Error processing {file_path}: {e}")
                continue
    
    return snippets

def create_code_snippets(parsed_data: List[Dict[str, Any]]) -> List[CodeSnippet]:
    """Convert parsed data to CodeSnippet entities."""
    snippets = []
    
    for idx, data in enumerate(parsed_data):
        try:
            snippet = create_snippet(
                code=data.get('code', ''),
                language=data.get('language', 'Unknown'),
                label=data.get('label'),
                source=data.get('source', 'unknown'),
                file_path=data.get('file_path', ''),
                context=data.get('context', ''),
                metadata={
                    'line_number': data.get('line_number'),
                    'cwe_id': data.get('cwe_id'),
                }
            )
            snippets.append(snippet)
        except Exception as e:
            logger.warning(f"Failed to create snippet from data: {e}")
            continue
    
    return snippets

def save_snippets_to_csv(snippets: List[CodeSnippet], output_path: Path) -> None:
    """Save CodeSnippets to CSV file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Write header
        writer.writerow([
            'snippet_id', 'code', 'language', 'label', 'source', 
            'file_path', 'context', 'metadata'
        ])
        
        # Write data
        for snippet in snippets:
            writer.writerow([
                snippet.snippet_id,
                snippet.code.replace('\n', '\\n').replace('\r', '\\r'),
                snippet.language,
                snippet.label,
                snippet.source,
                snippet.file_path,
                snippet.context.replace('\n', '\\n').replace('\r', '\\r'),
                json.dumps(snippet.metadata)
            ])
    
    logger.info(f"Saved {len(snippets)} snippets to {output_path}")

def log_edge_cases(snippets: List[CodeSnippet], log_path: Path) -> None:
    """Log edge cases (samples with missing labels) to features.log."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(f"\n--- Edge Case Log: {len(snippets)} samples processed ---\n")
        
        missing_label_count = 0
        for snippet in snippets:
            if snippet.label is None:
                missing_label_count += 1
                f.write(f"Snippet ID: {snippet.snippet_id}\n")
                f.write(f"  Language: {snippet.language}\n")
                f.write(f"  Source: {snippet.source}\n")
                f.write(f"  File: {snippet.file_path}\n")
                f.write(f"  Label: NULL (excluded from accuracy calculations)\n")
                f.write(f"  Features: null/invalid (edge case handling)\n")
                f.write("-" * 50 + "\n")
        
        f.write(f"Total samples with missing labels: {missing_label_count}\n")
        f.write(f"Total samples with valid labels: {len(snippets) - missing_label_count}\n")
        f.write("--- End Edge Case Log ---\n")
    
    logger.info(f"Logged {missing_label_count} edge cases to {log_path}")

def main():
    """Main entry point for preprocessing."""
    log_stage_start("preprocess", "Parsing raw datasets and extracting code snippets")
    
    try:
        # Define paths
        data_dir = Path("data/raw")
        processed_dir = Path("data/processed")
        log_path = processed_dir / "features.log"
        output_path = processed_dir / "snippets.csv"
        
        # Ensure directories exist
        data_dir.mkdir(parents=True, exist_ok=True)
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        all_snippets = []
        
        # Parse VulDeePecker (Python)
        vuldeepecker_path = data_dir / "vuldeepecker.jsonl"
        if vuldeepecker_path.exists():
            logger.info("Parsing VulDeePecker dataset...")
            vuldeepecker_data = parse_vuldeepecker_jsonl(vuldeepecker_path)
            all_snippets.extend(vuldeepecker_data)
            logger.info(f"Extracted {len(vuldeepecker_data)} snippets from VulDeePecker")
        
        # Parse BigVul (C and JavaScript)
        # Assuming BigVul is stored in JSON format with code and label fields
        bigvul_c_path = data_dir / "bigvul_c.json"
        if bigvul_c_path.exists():
            logger.info("Parsing BigVul C dataset...")
            with open(bigvul_c_path, 'r', encoding='utf-8', errors='ignore') as f:
                bigvul_c_data = json.load(f)
            
            # Convert to standard format
            for record in bigvul_c_data:
                all_snippets.append({
                    'code': record.get('code', ''),
                    'label': normalize_label(record.get('label')),
                    'language': 'C',
                    'context': record.get('context', ''),
                    'file_path': record.get('file', ''),
                    'source': 'BigVul_C',
                })
            logger.info(f"Extracted {len(bigvul_c_data)} snippets from BigVul C")
        
        bigvul_js_path = data_dir / "bigvul_js.json"
        if bigvul_js_path.exists():
            logger.info("Parsing BigVul JavaScript dataset...")
            with open(bigvul_js_path, 'r', encoding='utf-8', errors='ignore') as f:
                bigvul_js_data = json.load(f)
            
            for record in bigvul_js_data:
                all_snippets.append({
                    'code': record.get('code', ''),
                    'label': normalize_label(record.get('label')),
                    'language': 'JavaScript',
                    'context': record.get('context', ''),
                    'file_path': record.get('file', ''),
                    'source': 'BigVul_JS',
                })
            logger.info(f"Extracted {len(bigvul_js_data)} snippets from BigVul JavaScript")
        
        # Parse Juliet C test cases
        juliet_c_path = data_dir / "juliet_c"
        if juliet_c_path.exists():
            logger.info("Parsing Juliet C test cases...")
            juliet_c_data = parse_juliet_c_test_cases(juliet_c_path)
            all_snippets.extend(juliet_c_data)
            logger.info(f"Extracted {len(juliet_c_data)} snippets from Juliet C")
        
        # Parse Juliet Java test cases
        juliet_java_path = data_dir / "juliet_java"
        if juliet_java_path.exists():
            logger.info("Parsing Juliet Java test cases...")
            juliet_java_data = parse_juliet_java_test_cases(juliet_java_path)
            all_snippets.extend(juliet_java_data)
            logger.info(f"Extracted {len(juliet_java_data)} snippets from Juliet Java")
        
        # Create CodeSnippet entities
        logger.info("Creating CodeSnippet entities...")
        code_snippets = create_code_snippets(all_snippets)
        logger.info(f"Created {len(code_snippets)} CodeSnippet entities")
        
        # Save to CSV
        logger.info("Saving snippets to CSV...")
        save_snippets_to_csv(code_snippets, output_path)
        
        # Log edge cases (samples with missing labels)
        logger.info("Logging edge cases...")
        log_edge_cases(code_snippets, log_path)
        
        # Summary statistics
        valid_labels = sum(1 for s in code_snippets if s.label is not None)
        missing_labels = sum(1 for s in code_snippets if s.label is None)
        languages = set(s.language for s in code_snippets)
        
        logger.info(f"Preprocessing complete:")
        logger.info(f"  Total snippets: {len(code_snippets)}")
        logger.info(f"  Valid labels: {valid_labels}")
        logger.info(f"  Missing labels (edge cases): {missing_labels}")
        logger.info(f"  Languages: {', '.join(languages)}")
        
        log_stage_complete("preprocess", f"Processed {len(code_snippets)} snippets")
        
    except Exception as e:
        log_stage_failure("preprocess", str(e))
        raise

if __name__ == "__main__":
    main()
