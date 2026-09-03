import os
import re
from pathlib import Path
from typing import List, Dict

def find_hardcoded_paths(root_dir: str) -> List[Dict[str, str]]:
    """Find hardcoded path strings in Python files."""
    patterns = [
        r'"data/raw"',
        r"'data/raw'",
        r'"data/processed"',
        r"'data/processed'",
        r'"output/figures"',
        r"'output/figures'",
        r'"output/reports"',
        r"'output/reports'",
        r'"output"',
        r"'output'"
    ]
    
    findings = []
    root_path = Path(root_dir)
    
    for py_file in root_path.rglob("*.py"):
        if "test" in str(py_file) or "__pycache__" in str(py_file):
            continue
        
        with open(py_file, 'r') as f:
            content = f.read()
            
        for pattern in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                # Check if it's in a comment or string
                line_start = content.rfind('\n', 0, match.start()) + 1
                line_end = content.find('\n', match.end())
                if line_end == -1:
                    line_end = len(content)
                line = content[line_start:line_end]
                
                # Skip if it's in a comment
                if line.strip().startswith('#'):
                    continue
                
                # Skip if it's an import or config reference
                if 'import' in line or 'config' in line.lower():
                    continue
                
                findings.append({
                    "file": str(py_file),
                    "line": line,
                    "pattern": pattern
                })
    
    return findings

def main():
    """Main entry point."""
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    findings = find_hardcoded_paths("code")
    
    if findings:
        logger.error(f"Found {len(findings)} hardcoded paths:")
        for f in findings:
            logger.error(f"  {f['file']}: {f['line'].strip()}")
        return 1
    else:
        logger.info("No hardcoded paths found. All paths use config.py.")
        return 0

if __name__ == "__main__":
    exit(main())