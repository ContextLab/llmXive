import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from radon.complexity import cc_visit, cc_visit_ast

from utils.logger import get_logger

# Initialize logger for this module
logger = get_logger(__name__)

# Supported file extensions for analysis
SUPPORTED_EXTENSIONS = {'.py', '.java'}

class CodeSnippetMetrics:
    """Data class to hold complexity and documentation metrics for a code snippet."""
    def __init__(self, file_path: str, cyclomatic_complexity: float, 
                 documentation_density: float, total_lines: int, 
                 comment_lines: int, language: str):
        self.file_path = file_path
        self.cyclomatic_complexity = cyclomatic_complexity
        self.documentation_density = documentation_density
        self.total_lines = total_lines
        self.comment_lines = comment_lines
        self.language = language

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "cyclomatic_complexity": self.cyclomatic_complexity,
            "documentation_density": self.documentation_density,
            "total_lines": self.total_lines,
            "comment_lines": self.comment_lines,
            "language": self.language
        }

def calculate_cyclomatic_complexity(source_code: str, language: str) -> float:
    """
    Calculate Cyclomatic Complexity using radon.
    
    Args:
        source_code: The source code string.
        language: The programming language ('python' or 'java').
        
    Returns:
        The cyclomatic complexity score.
        
    Raises:
        ValueError: If the language is not supported or parsing fails.
    """
    if language.lower() == 'python':
        # radon expects Python source code
        try:
            results = cc_visit(source_code)
            if not results:
                return 0.0
            # Return the maximum complexity found in the file
            return max(r.complexity for r in results)
        except Exception as e:
            logger.warning(f"Failed to analyze complexity for Python code: {e}")
            return 0.0
    elif language.lower() == 'java':
        # radon has limited Java support via cc_visit_ast if parsed, 
        # but standard cc_visit is Python-only. 
        # For Java, we might need a different approach or return 0 if unsupported by radon directly.
        # Given the constraints and radon's primary focus on Python, 
        # we will attempt to use it but log a warning if it fails or isn't applicable.
        # Note: radon.complexity.cc_visit is strictly for Python. 
        # For Java, we might need a fallback or external tool, but per task constraints 
        # we use radon. If radon cannot handle Java, we return 0 or raise.
        # To be robust, we'll check if radon can handle it. If not, we log and return 0.
        logger.warning("Radon's cc_visit is primarily for Python. Java complexity may be inaccurate or 0.")
        try:
            results = cc_visit(source_code)
            if not results:
                return 0.0
            return max(r.complexity for r in results)
        except Exception as e:
            logger.warning(f"Failed to analyze Java complexity with radon: {e}")
            return 0.0
    else:
        raise ValueError(f"Unsupported language for complexity calculation: {language}")

def calculate_documentation_density(source_code: str, language: str) -> Tuple[int, int]:
    """
    Calculate documentation density (comment lines / total lines).
    
    Args:
        source_code: The source code string.
        language: The programming language ('python' or 'java').
        
    Returns:
        A tuple of (comment_lines, total_lines).
    """
    lines = source_code.splitlines()
    total_lines = len(lines)
    if total_lines == 0:
        return 0, 0
    
    comment_lines = 0
    in_multiline_comment = False
    
    for line in lines:
        stripped = line.strip()
        
        if language.lower() == 'python':
            if in_multiline_comment:
                comment_lines += 1
                if '"""' in stripped or "'''" in stripped:
                    in_multiline_comment = False
            else:
                if stripped.startswith('#'):
                    comment_lines += 1
                elif stripped.startswith('"""') or stripped.startswith("'''"):
                    comment_lines += 1
                    # Check if it closes on the same line
                    if stripped.count('"""') == 2 or stripped.count("'''") == 2:
                        pass # Single line docstring, already counted
                    else:
                        in_multiline_comment = True
                        # If it ends on the same line (e.g. """..."""), don't set flag
                        if (stripped.startswith('"""') and '"""' in stripped[3:]) or \
                           (stripped.startswith("'''") and "'''" in stripped[3:]):
                            in_multiline_comment = False
                            
        elif language.lower() == 'java':
            if in_multiline_comment:
                comment_lines += 1
                if '*/' in stripped:
                    in_multiline_comment = False
            else:
                if stripped.startswith('//'):
                    comment_lines += 1
                elif stripped.startswith('/*'):
                    comment_lines += 1
                    if '*/' not in stripped:
                        in_multiline_comment = True
        else:
            # Default to Python-like if unknown
            if stripped.startswith('#'):
                comment_lines += 1
                
    return comment_lines, total_lines

def process_snippet(file_path: Path, language: str) -> Optional[CodeSnippetMetrics]:
    """
    Process a single code snippet file.
    
    Args:
        file_path: Path to the file.
        language: The programming language.
        
    Returns:
        CodeSnippetMetrics object or None if processing fails.
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            source_code = f.read()
        
        if not source_code.strip():
            logger.warning(f"File {file_path} is empty.")
            return None

        cc = calculate_cyclomatic_complexity(source_code, language)
        comment_lines, total_lines = calculate_documentation_density(source_code, language)
        
        doc_density = comment_lines / total_lines if total_lines > 0 else 0.0
        
        return CodeSnippetMetrics(
            file_path=str(file_path),
            cyclomatic_complexity=cc,
            documentation_density=doc_density,
            total_lines=total_lines,
            comment_lines=comment_lines,
            language=language
        )
    except Exception as e:
        logger.error(f"Failed to process snippet {file_path}: {e}")
        return None

def extract_metrics_from_directory(directory: Path) -> List[CodeSnippetMetrics]:
    """
    Extract metrics from all supported files in a directory.
    Filters out non-Python/Java files.
    
    Args:
        directory: The directory to scan.
        
    Returns:
        List of CodeSnippetMetrics objects.
    """
    metrics_list = []
    
    if not directory.exists():
        logger.error(f"Directory does not exist: {directory}")
        return metrics_list
        
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = Path(root) / file
            ext = file_path.suffix.lower()
            
            # FILTERING LOGIC: Skip non-Python/Java files
            if ext not in SUPPORTED_EXTENSIONS:
                logger.warning(f"Skipping non-supported file: {file_path} (extension: {ext})")
                continue
            
            language = 'python' if ext == '.py' else 'java'
            logger.info(f"Processing {file_path} as {language}")
            
            metrics = process_snippet(file_path, language)
            if metrics:
                metrics_list.append(metrics)
                
    return metrics_list

def save_metrics_to_json(metrics_list: List[CodeSnippetMetrics], output_path: Path) -> None:
    """
    Save metrics to a JSON file.
    
    Args:
        metrics_list: List of CodeSnippetMetrics.
        output_path: Path to the output JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    data = [m.to_dict() for m in metrics_list]
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
        
    logger.info(f"Saved {len(data)} metrics to {output_path}")

def main():
    """Main entry point for the complexity extractor."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract code complexity and documentation metrics.")
    parser.add_argument("--input-dir", type=str, required=True, help="Directory containing code snippets")
    parser.add_argument("--output-file", type=str, required=True, help="Output JSON file path")
    
    args = parser.parse_args()
    
    input_dir = Path(args.input_dir)
    output_file = Path(args.output_file)
    
    logger.info(f"Starting extraction from {input_dir} to {output_file}")
    
    metrics = extract_metrics_from_directory(input_dir)
    save_metrics_to_json(metrics, output_file)
    
    logger.info("Extraction complete.")

if __name__ == "__main__":
    main()