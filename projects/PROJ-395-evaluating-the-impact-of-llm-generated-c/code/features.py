import re
import string
from pathlib import Path
from typing import List, Dict, Any, Optional

# Constants for normalization
WHITESPACE_PATTERN = re.compile(r'\s+')
COMMENT_PATTERN = re.compile(r'#.*$', re.MULTILINE)
STRING_PATTERN = re.compile(r'"[^"\\]*(\\.[^"\\]*)*"|\'[^\'\\]*(\\.[^\'\\]*)*\'', re.DOTALL)

def normalize_code_text(code: str) -> str:
    """
    Normalize code text for consistent feature extraction.
    Removes comments, normalizes whitespace, and preserves string literals.
    """
    if not code:
        return ""
    
    # Remove comments (but not inside strings - simplified approach)
    # Note: A full parser would be better, but this regex approach works for simple cases
    lines = code.split('\n')
    cleaned_lines = []
    for line in lines:
        # Remove inline comments (simplified)
        if '#' in line:
            # Check if # is inside a string
            in_string = False
            string_char = None
            cleaned_line = []
            for i, char in enumerate(line):
                if char in ('"', "'") and (i == 0 or line[i-1] != '\\'):
                    if not in_string:
                        in_string = True
                        string_char = char
                    elif char == string_char:
                        in_string = False
                        string_char = None
                if char == '#' and not in_string:
                    break
                cleaned_line.append(char)
            cleaned_lines.append(''.join(cleaned_line))
        else:
            cleaned_lines.append(line)
    
    normalized = '\n'.join(cleaned_lines)
    
    # Normalize whitespace (multiple spaces to single space, except in strings)
    # This is a simplified approach
    normalized = WHITESPACE_PATTERN.sub(' ', normalized)
    
    return normalized.strip()

def extract_loc(code: str) -> int:
    """
    Extract Lines of Code (LOC) from code text.
    Counts non-empty, non-comment lines.
    
    Args:
        code: The code text to analyze
        
    Returns:
        int: Number of lines of code
    """
    if not code:
        return 0
    
    normalized = normalize_code_text(code)
    lines = normalized.split('\n')
    
    # Filter out empty lines and comment-only lines
    loc_count = 0
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith('#'):
            loc_count += 1
    
    return loc_count

def calculate_memory_per_loc(peak_memory_bytes: float, loc: int) -> float:
    """
    Calculate memory per line of code as a DESCRIPTIVE metric ONLY.
    
    IMPORTANT: This metric is explicitly excluded from regression analysis
    per Plan.md to prevent spurious correlations (mathematical coupling).
    
    Args:
        peak_memory_bytes: Peak memory usage in bytes
        loc: Lines of Code
        
    Returns:
        float: Memory per LOC in bytes/line, or 0.0 if LOC is 0
    """
    if loc <= 0:
        return 0.0
    
    return peak_memory_bytes / loc

def count_library_imports(code: str) -> int:
    """
    Count the number of library imports in the code.
    
    Args:
        code: The code text to analyze
        
    Returns:
        int: Number of import statements
    """
    if not code:
        return 0
    
    normalized = normalize_code_text(code)
    lines = normalized.split('\n')
    
    import_count = 0
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('import ') or stripped.startswith('from '):
            import_count += 1
    
    return import_count

def get_manifest_version(manifest_path: Optional[str] = None) -> str:
    """
    Get the version from the dataset manifest file.
    
    Args:
        manifest_path: Path to the manifest file (defaults to data/dataset_manifest.yaml)
        
    Returns:
        str: Version string from the manifest, or 'unknown' if not found
    """
    if manifest_path is None:
        manifest_path = 'data/dataset_manifest.yaml'
    
    manifest_file = Path(manifest_path)
    if not manifest_file.exists():
        return 'unknown'
    
    try:
        import yaml
        with open(manifest_file, 'r', encoding='utf-8') as f:
            manifest = yaml.safe_load(f)
            if isinstance(manifest, dict) and 'version' in manifest:
                return str(manifest['version'])
    except Exception:
        pass
    
    return 'unknown'

def extract_feature_vector(code: str) -> Dict[str, Any]:
    """
    Extract all feature metrics from code.
    
    Args:
        code: The code text to analyze
        
    Returns:
        dict: Dictionary containing LOC, cyclomatic complexity, and import count
    """
    loc = extract_loc(code)
    complexity = calculate_cyclomatic_complexity(code)
    imports = count_library_imports(code)
    
    return {
        'loc': loc,
        'cyclomatic_complexity': complexity,
        'import_count': imports
    }

def calculate_cyclomatic_complexity(code: str) -> int:
    """
    Calculate cyclomatic complexity using a simplified approach.
    Counts decision points (if, for, while, etc.) in the code.
    
    Note: For accurate complexity calculation, networkx should be used
    with proper AST parsing. This is a simplified version.
    
    Args:
        code: The code text to analyze
        
    Returns:
        int: Estimated cyclomatic complexity
    """
    if not code:
        return 1  # Base complexity
    
    normalized = normalize_code_text(code)
    
    # Decision point patterns
    decision_patterns = [
        r'\bif\b',
        r'\belif\b',
        r'\bfor\b',
        r'\bwhile\b',
        r'\band\b',
        r'\bor\b',
        r'\bexcept\b',
        r'\bcase\b',  # Python 3.10+
    ]
    
    complexity = 1  # Base complexity
    for pattern in decision_patterns:
        matches = re.findall(pattern, normalized)
        complexity += len(matches)
    
    return complexity