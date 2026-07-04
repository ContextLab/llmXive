"""
Task T032: Remove all 8-bit/4-bit quantization imports and verify no CUDA imports.

This script scans the project's Python source tree for prohibited imports
related to 8-bit/4-bit quantization (bitsandbytes, deepspeed, etc.) and
CUDA-specific imports. It generates a report of findings and can optionally
remove the prohibited lines.
"""
from __future__ import annotations

import pathlib
import re
import sys
from datetime import datetime
from typing import List, Dict, Set, Tuple, Optional

# Prohibited patterns for 8-bit/4-bit quantization
QUANTIZATION_PATTERNS = [
    r"from\s+bitsandbytes",
    r"import\s+bitsandbytes",
    r"from\s+deepspeed",
    r"import\s+deepspeed",
    r"from\s+optimum\.int",
    r"import\s+optimum\.int",
    r"from\s+transformers\.utils\s+import.*bitsandbytes",
    r"load_in_8bit",
    r"load_in_4bit",
    r"bnb",
    r"nf4",
    r"fp4",
    r"int8",
    r"int4",
]

# Prohibited patterns for CUDA
CUDA_PATTERNS = [
    r"import\s+torch\.cuda",
    r"from\s+torch\.cuda",
    r"\.cuda\(",
    r"\.to\('cuda'",
    r"\.to\(\"cuda\"",
    r"device\s*=\s*['\"]cuda",
    r"torch\.cuda\.is_available",
    r"torch\.cuda\.empty_cache",
    r"torch\.cuda\.max_memory_allocated",
    r"torch\.cuda\.current_device",
    r"torch\.set_default_tensor_type\(['\"]CUDA",
]

# Allowed exceptions (common patterns that might look like CUDA but aren't)
ALLOWED_PATTERNS = [
    r"#\s*TODO.*cuda",
    r"#\s*FIXME.*cuda",
    r"if.*cuda.*:.*pass",  # Comments or empty blocks
    r"print.*cuda",
]

def is_prohibited_line(line: str, line_num: int, file_path: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Check if a line contains prohibited quantization or CUDA imports.
    
    Args:
        line: The line of code to check
        line_num: Line number in the file
        file_path: Path to the file being checked
        
    Returns:
        Tuple of (is_prohibited, pattern_type, pattern_matched)
    """
    # Skip empty lines and comments
    stripped = line.strip()
    if not stripped or stripped.startswith('#'):
        return False, None, None
        
    # Check for quantization patterns
    for pattern in QUANTIZATION_PATTERNS:
        if re.search(pattern, line, re.IGNORECASE):
            # Check if it's in a comment or allowed pattern
            is_allowed = False
            for allowed in ALLOWED_PATTERNS:
                if re.search(allowed, line, re.IGNORECASE):
                    is_allowed = True
                    break
            if not is_allowed:
                return True, "quantization", pattern
                
    # Check for CUDA patterns
    for pattern in CUDA_PATTERNS:
        if re.search(pattern, line, re.IGNORECASE):
            # Check if it's in a comment or allowed pattern
            is_allowed = False
            for allowed in ALLOWED_PATTERNS:
                if re.search(allowed, line, re.IGNORECASE):
                    is_allowed = True
                    break
            if not is_allowed:
                return True, "cuda", pattern
                
    return False, None, None

def process_file(file_path: pathlib.Path, remove_prohibited: bool = False) -> Dict:
    """
    Process a single Python file for prohibited imports.
    
    Args:
        file_path: Path to the Python file
        remove_prohibited: If True, remove prohibited lines from the file
        
    Returns:
        Dictionary with file analysis results
    """
    findings = []
    lines = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        return {
            "file": str(file_path),
            "error": str(e),
            "findings": [],
            "status": "error"
        }
    
    new_lines = []
    for i, line in enumerate(lines, 1):
        is_prohibited, pattern_type, pattern = is_prohibited_line(line, i, str(file_path))
        
        if is_prohibited:
            findings.append({
                "line": i,
                "content": line.strip(),
                "pattern_type": pattern_type,
                "pattern": pattern
            })
            
            if not remove_prohibited:
                new_lines.append(line)
        else:
            new_lines.append(line)
    
    # Write back if removing prohibited lines
    if remove_prohibited and findings:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            status = "modified"
        except Exception as e:
            status = "error"
            findings.append({
                "line": 0,
                "content": "",
                "pattern_type": "error",
                "pattern": f"Failed to write file: {e}"
            })
    else:
        status = "clean" if not findings else "findings_found"
        
    return {
        "file": str(file_path),
        "findings": findings,
        "status": status,
        "lines_processed": len(lines)
    }

def scan_project(root_dir: pathlib.Path, remove_prohibited: bool = False) -> List[Dict]:
    """
    Scan all Python files in the project directory.
    
    Args:
        root_dir: Root directory of the project
        remove_prohibited: If True, remove prohibited lines from files
        
    Returns:
        List of analysis results for each file
    """
    results = []
    python_files = list(root_dir.rglob("*.py"))
    
    print(f"Scanning {len(python_files)} Python files in {root_dir}...")
    
    for py_file in python_files:
        # Skip test files and __pycache__
        if "test" in py_file.parts or "__pycache__" in py_file.parts:
            continue
            
        result = process_file(py_file, remove_prohibited)
        results.append(result)
        
        if result["findings"]:
            print(f"  ⚠ {py_file.relative_to(root_dir)}: {len(result['findings'])} findings")
        elif result["status"] == "error":
            print(f"  ✗ {py_file.relative_to(root_dir)}: {result.get('error', 'Unknown error')}")
        else:
            print(f"  ✓ {py_file.relative_to(root_dir)}: clean")
            
    return results

def generate_markdown_report(results: List[Dict], output_path: pathlib.Path) -> None:
    """
    Generate a markdown report of the analysis.
    
    Args:
        results: List of file analysis results
        output_path: Path to write the markdown report
    """
    report_lines = [
        "# Quantization and CUDA Import Analysis Report",
        f"Generated: {datetime.now().isoformat()}",
        "",
        "## Summary",
        ""
    ]
    
    total_files = len(results)
    clean_files = sum(1 for r in results if r["status"] == "clean")
    files_with_findings = sum(1 for r in results if r["status"] == "findings_found")
    files_with_errors = sum(1 for r in results if r["status"] == "error")
    modified_files = sum(1 for r in results if r["status"] == "modified")
    
    report_lines.extend([
        f"- **Total files scanned**: {total_files}",
        f"- **Clean files**: {clean_files}",
        f"- **Files with findings**: {files_with_findings}",
        f"- **Files with errors**: {files_with_errors}",
        f"- **Files modified (prohibited imports removed)**: {modified_files}",
        ""
    ])
    
    if files_with_findings > 0:
        report_lines.extend([
            "## Findings by File",
            ""
        ])
        
        for result in results:
            if result["findings"]:
                report_lines.append(f"### {result['file']}")
                report_lines.append("")
                for finding in result["findings"]:
                    report_lines.append(f"- **Line {finding['line']}** ({finding['pattern_type']}): `{finding['pattern']}`")
                    report_lines.append(f"  - Content: `{finding['content']}`")
                report_lines.append("")
    
    if files_with_errors > 0:
        report_lines.extend([
            "## Errors",
            ""
        ])
        for result in results:
            if result["status"] == "error":
                report_lines.append(f"- **{result['file']}**: {result.get('error', 'Unknown error')}")
        report_lines.append("")
        
    report_lines.extend([
        "## Conclusion",
        ""
    ])
    
    if files_with_findings == 0 and files_with_errors == 0:
        report_lines.append("✅ All Python files are clean. No prohibited quantization or CUDA imports found.")
    elif files_with_findings > 0 and modified_files > 0:
        report_lines.append(f"✅ Prohibited imports have been removed from {modified_files} files.")
    elif files_with_findings > 0:
        report_lines.append(f"⚠️ {files_with_findings} files contain prohibited imports. Review the findings above.")
    else:
        report_lines.append("❌ Errors occurred during scanning. Review the errors above.")
        
    report_lines.append("")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
        
    print(f"\nReport written to {output_path}")

def main():
    """Main entry point for the script."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Scan project for prohibited quantization and CUDA imports"
    )
    parser.add_argument(
        "--remove",
        action="store_true",
        help="Remove prohibited imports from files"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/quantization_scan_report.md",
        help="Output path for the markdown report"
    )
    
    args = parser.parse_args()
    
    # Determine project root (assuming this script is in code/)
    script_path = pathlib.Path(__file__).resolve()
    project_root = script_path.parent.parent
    
    print(f"Project root: {project_root}")
    print(f"Remove prohibited imports: {args.remove}")
    print("")
    
    results = scan_project(project_root, remove_prohibited=args.remove)
    
    # Generate report
    output_path = project_root / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    generate_markdown_report(results, output_path)
    
    # Exit with error code if findings remain
    files_with_findings = sum(1 for r in results if r["status"] == "findings_found")
    if files_with_findings > 0:
        print(f"\n❌ {files_with_findings} files still contain prohibited imports.")
        sys.exit(1)
    else:
        print("\n✅ All files are clean.")
        sys.exit(0)

if __name__ == "__main__":
    main()