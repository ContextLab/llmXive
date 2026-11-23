"""
Task T013: Implement code/01_style_scoring.py

This script calculates style consistency metrics for Python files using pylint
(for indentation and naming) and radon (for line length). It also extracts
file_size and cyclomatic_complexity.

Outputs:
    data/metadata/style_scores_raw.csv
"""
import subprocess
import sys
import json
import os
import csv
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# Import utilities from existing project files to ensure API consistency
# T009 provides these functions: get_file_age_git, get_file_size, get_cyclomatic_complexity, find_python_files
# Since 01_style_scoring.py is in code/, we import from the sibling module
try:
    from code.utils import metrics  # Importing to ensure utils exists, though not used for scores directly here
except ImportError:
    pass

# We need to import the specific functions from 00_extract_metadata
# Since they are in the same directory 'code/', we can import them directly if we treat code as a package
# or use relative imports if running as a module. To be safe and robust as a script:
# We will implement the logic here or import from the sibling file by adding the path.

# However, the prompt says: "import the real names that sibling files already define"
# The API surface for 00_extract_metadata lists: get_file_size, get_cyclomatic_complexity
# We will attempt to import them. If the environment treats 'code' as a package, we use code.00_extract_metadata.
# If it's a flat script execution, we might need to adjust sys.path.

# Let's assume the standard project structure where we can import sibling modules in the same directory.
# To be safe for the runner, we will try importing from the sibling module directly.

import importlib.util
import sys

def load_sibling_module(module_name: str, file_path: Path):
    """Dynamically load a sibling module to access its functions."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    return None

# Load the 00_extract_metadata module to reuse its functions
metadata_module_path = Path(__file__).parent / "00_extract_metadata.py"
if metadata_module_path.exists():
    metadata_mod = load_sibling_module("00_extract_metadata", metadata_module_path)
    get_file_size = getattr(metadata_mod, 'get_file_size', None)
    get_cyclomatic_complexity = getattr(metadata_mod, 'get_cyclomatic_complexity', None)
    find_python_files = getattr(metadata_mod, 'find_python_files', None)
else:
    # Fallback: implement basic versions if the module is missing (though T009 should exist)
    get_file_size = None
    get_cyclomatic_complexity = None
    find_python_files = None

def get_file_size_fallback(file_path: Path) -> int:
    """Fallback to get file size in bytes."""
    return file_path.stat().st_size

def get_cyclomatic_complexity_fallback(file_path: Path) -> float:
    """
    Fallback to calculate cyclomatic complexity using radon.
    If radon is not available or fails, return 0.0.
    """
    try:
        from radon.complexity import cc_visit
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            source = f.read()
        results = cc_visit(source)
        if not results:
            return 0.0
        # Return average complexity
        total = sum(r.complexity for r in results)
        return total / len(results)
    except Exception:
        return 0.0

def get_pylint_score(file_path: Path) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    """
    Run pylint on a file and extract indentation and naming scores.
    Returns: (indentation_score, naming_score, overall_score)
    If pylint fails, returns (None, None, None).
    """
    try:
        # Run pylint with JSON output
        result = subprocess.run(
            [sys.executable, "-m", "pylint", "--output-format=json", str(file_path)],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode not in (0, 16): # 0 = OK, 16 = syntax error but parsed
            # If it's a major failure (e.g. file not found), return None
            if "No such file" in result.stderr:
                return None, None, None
            # For other errors, we might still have JSON if it parsed
        
        try:
            messages = json.loads(result.stdout)
        except json.JSONDecodeError:
            return None, None, None

        # Pylint scores are not directly in the JSON messages list as "score".
        # We need to calculate based on messages or use the --score option if available in output.
        # Actually, pylint's JSON output doesn't include the final score by default in the list of messages.
        # We need to parse the "refactor" or "convention" messages to estimate.
        # However, a simpler approach for "style" is to count specific message types.
        
        # Let's try to get the score by running pylint with --score=yes (default) and parsing the summary if available,
        # but the JSON output is a list of messages.
        # Alternative: Use pylint's --reports=no and parse the summary line? No, we need JSON.
        
        # Strategy: Calculate a normalized score based on message counts for specific categories.
        # Categories of interest:
        # - indentation (C0301, C0303, C0304, etc. - actually C03 is convention)
        # - naming (C0103, C0111, etc.)
        
        # Let's count violations for specific groups.
        # Max score is 10.0.
        
        convention_messages = [m for m in messages if m['type'] == 'convention']
        refactor_messages = [m for m in messages if m['type'] == 'refactor']
        
        # Specific codes for indentation/naming in 'convention'
        # Indentation: C0301, C0302, C0303, C0304, C0325, C0326, C0327, C0328
        # Naming: C0103, C0111, C0112, C0113, C0114, C0115, C0116
        
        indentation_codes = {'C0301', 'C0302', 'C0303', 'C0304', 'C0325', 'C0326', 'C0327', 'C0328', 'C0305', 'C0306'}
        naming_codes = {'C0103', 'C0111', 'C0112', 'C0113', 'C0114', 'C0115', 'C0116'}
        
        indent_count = sum(1 for m in convention_messages if m['symbol'] in indentation_codes or any(c in m['message'] for c in ['indent', 'line too long'])) 
        # Note: 'line too long' is C0301. 
        # Actually, let's just count specific symbols.
        indent_count = sum(1 for m in convention_messages if m['symbol'].startswith('C030') or m['symbol'] in {'C0325', 'C0326', 'C0327', 'C0328'})
        naming_count = sum(1 for m in convention_messages if m['symbol'].startswith('C010') or m['symbol'].startswith('C011'))
        
        # Normalize: Assume 10 violations = 0 score. Cap at 10.
        # This is a heuristic.
        indent_score = max(0.0, 10.0 - (indent_count * 1.0))
        naming_score = max(0.0, 10.0 - (naming_count * 1.0))
        
        # Overall style score could be average of these two, or based on total convention messages
        # Let's use the average of the two specific scores for "style consistency"
        overall_score = (indent_score + naming_score) / 2.0
        
        return indent_score, naming_score, overall_score

    except subprocess.TimeoutExpired:
        return None, None, None
    except Exception:
        return None, None, None

def get_radon_line_length_score(file_path: Path) -> Optional[float]:
    """
    Run radon to check line length (C0301 equivalent).
    Returns a score (0-10) based on line length violations.
    """
    try:
        from radon.complexity import cc_visit
        from radon.visitors import ComplexityVisitor
        from radon.metrics import h_visit
        # Radon doesn't have a direct "line length" score in the same way as pylint.
        # We can check for long lines using radon's raw metrics or just parse the file.
        # Let's count lines > 120 chars.
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        long_lines = sum(1 for line in lines if len(line.strip()) > 120)
        
        # Score: 10 - (long_lines * 0.5), min 0
        score = max(0.0, 10.0 - (long_lines * 0.5))
        return score
    except Exception:
        return None

def compute_style_score(indent_score: Optional[float], naming_score: Optional[float], line_len_score: Optional[float]) -> Optional[float]:
    """
    Compute a composite style score from the individual metrics.
    Returns None if any critical metric is missing.
    """
    if indent_score is None or naming_score is None or line_len_score is None:
        return None
    
    # Weighted average: 40% indent, 40% naming, 20% line length
    composite = (indent_score * 0.4) + (naming_score * 0.4) + (line_len_score * 0.2)
    # Normalize to 0-1 range for consistency with project goals (0.0-1.0)
    return composite / 10.0

def main():
    """Main entry point for style scoring."""
    # Determine target directory (default to current repo root or a specific data dir if provided)
    # The task implies scanning the project's source code.
    # We'll scan the 'code' directory or the root if 'code' is not the target.
    # Let's assume we scan the project root for Python files, excluding data/ and tests/ if needed,
    # but the task says "all source files". Let's scan the 'code' directory as it's the source.
    
    base_dir = Path(__file__).parent.parent
    source_dir = base_dir / "code"
    
    if not source_dir.exists():
        print(f"Source directory not found: {source_dir}")
        sys.exit(1)
    
    # Find all Python files
    if find_python_files:
        python_files = list(find_python_files(source_dir))
    else:
        # Fallback implementation
        python_files = list(source_dir.rglob("*.py"))
    
    if not python_files:
        print("No Python files found.")
        sys.exit(0)
    
    results = []
    errors = []
    
    for file_path in python_files:
        try:
            # Get file size
            if get_file_size:
                size = get_file_size(file_path)
            else:
                size = get_file_size_fallback(file_path)
            
            # Get cyclomatic complexity
            if get_cyclomatic_complexity:
                complexity = get_cyclomatic_complexity(file_path)
            else:
                complexity = get_cyclomatic_complexity_fallback(file_path)
            
            # Get pylint scores
            indent_score, naming_score, overall_pylint = get_pylint_score(file_path)
            
            # Get radon line length score
            line_len_score = get_radon_line_length_score(file_path)
            
            # Compute composite
            composite = compute_style_score(indent_score, naming_score, line_len_score)
            
            if composite is None:
                errors.append(str(file_path))
                continue
            
            results.append({
                "file_path": str(file_path),
                "pylint_indent": round(indent_score, 2) if indent_score is not None else None,
                "pylint_naming": round(naming_score, 2) if naming_score is not None else None,
                "radon_line_len": round(line_len_score, 2) if line_len_score is not None else None,
                "composite_score": round(composite, 4),
                "file_size": size,
                "cyclomatic_complexity": round(complexity, 2),
                "status": "ok"
            })
            
        except Exception as e:
            errors.append(f"{file_path}: {str(e)}")
            continue
    
    # Write output to CSV
    output_dir = base_dir / "data" / "metadata"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "style_scores_raw.csv"
    
    if results:
        fieldnames = ["file_path", "pylint_indent", "pylint_naming", "radon_line_len", "composite_score", "file_size", "cyclomatic_complexity", "status"]
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        print(f"Successfully wrote {len(results)} records to {output_file}")
    else:
        print("No valid style scores computed.")
    
    if errors:
        print(f"Encountered {len(errors)} errors:")
        for err in errors[:10]: # Log first 10
            print(f"  {err}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
