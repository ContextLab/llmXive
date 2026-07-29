"""
Preprocess downloaded code chunks using CodeQL and tree-sitter.

This module implements T016:
- Creates queries/complexity.ql for cyclomatic complexity, nesting depth, and repetition ratio.
- Processes files in data/processed/train_python/ and data/processed/val_java/.
- Skips unparseable files and logs errors (Edge Case 1).
- Outputs annotated JSONL files.
"""

import json
import logging
import os
import sys
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Local imports matching API surface
from config import get_config
from utils.logging import get_logger, ParseError, handle_parse_error
from contracts.schemas import CodeChunk

logger = get_logger(__name__)
CONFIG = get_config()

# Constants
COMPLEXITY_QL_QUERY = """
// Complexity metrics query for CodeQL
// Measures: cyclomatic complexity, nesting depth, repetition ratio

import python
import java

// Cyclomatic Complexity: count decision points (if, while, for, etc.)
predicate hasCyclomaticComplexity(
  Function f,
  int complexity
) {
  complexity = f.getNumberOfDecisionPoints() + 1
}

// Nesting Depth: maximum nesting level of control structures
predicate hasNestingDepth(
  Function f,
  int depth
) {
  depth = f.getMaxNestingDepth()
}

// Repetition Ratio: ratio of repeated statements/lines
predicate hasRepetitionRatio(
  Function f,
  float ratio
) {
  // Placeholder: actual implementation would count repeated patterns
  ratio = 0.0
}
"""

def ensure_codeql_available() -> bool:
    """Check if CodeQL CLI is available in PATH."""
    try:
        result = subprocess.run(
            ["codeql", "version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            logger.info("CodeQL CLI is available")
            return True
        else:
            logger.warning("CodeQL CLI found but returned error: %s", result.stderr)
            return False
    except FileNotFoundError:
        logger.warning("CodeQL CLI not found in PATH")
        return False
    except subprocess.TimeoutExpired:
        logger.warning("CodeQL version check timed out")
        return False
    except Exception as e:
        logger.warning("Error checking CodeQL: %s", str(e))
        return False

def create_complexity_query_file() -> Path:
    """Create the complexity.ql query file in queries/ directory."""
    queries_dir = Path(CONFIG["project_root"]) / "queries"
    queries_dir.mkdir(exist_ok=True)
    
    query_file = queries_dir / "complexity.ql"
    with open(query_file, "w", encoding="utf-8") as f:
        f.write(COMPLEXITY_QL_QUERY)
    
    logger.info("Created complexity query file: %s", query_file)
    return query_file

def run_codeql_analysis(
    source_file: Path,
    language: str,
    output_dir: Path
) -> Optional[Dict[str, Any]]:
    """
    Run CodeQL analysis on a single file.
    
    Args:
        source_file: Path to the source file
        language: 'python' or 'java'
        output_dir: Directory to store analysis results
        
    Returns:
        Dictionary with complexity metrics or None if analysis fails
    """
    if not ensure_codeql_available():
        logger.warning("Skipping CodeQL analysis for %s: CodeQL not available", source_file)
        return None
    
    try:
        # Create a temporary database
        with tempfile.TemporaryDirectory() as tmp_db:
            db_path = Path(tmp_db) / "db"
            
            # Create database
            logger.debug("Creating CodeQL database for %s", source_file)
            db_result = subprocess.run(
                [
                    "codeql", "database", "create", str(db_path),
                    "--language", language,
                    "--source-root", str(source_file.parent),
                    "--overwrite"
                ],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if db_result.returncode != 0:
                logger.warning("CodeQL database creation failed for %s: %s", 
                             source_file, db_result.stderr)
                return None
            
            # Run query
            query_file = create_complexity_query_file()
            output_csv = output_dir / f"{source_file.stem}_results.csv"
            
            logger.debug("Running CodeQL query on %s", source_file)
            query_result = subprocess.run(
                [
                    "codeql", "database", "analyze", str(db_path),
                    query_file,
                    f"--format=csv",
                    f"--output={output_csv}"
                ],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if query_result.returncode != 0:
                logger.warning("CodeQL query failed for %s: %s", 
                             source_file, query_result.stderr)
                return None
            
            # Parse results
            if output_csv.exists():
                return parse_codeql_results(output_csv)
            else:
                logger.warning("No output file generated for %s", source_file)
                return None
    
    except subprocess.TimeoutExpired:
        logger.warning("CodeQL analysis timed out for %s", source_file)
        return None
    except Exception as e:
        logger.warning("Error during CodeQL analysis for %s: %s", source_file, str(e))
        return None

def parse_codeql_results(csv_path: Path) -> Dict[str, Any]:
    """Parse CodeQL CSV output into metrics dictionary."""
    metrics = {
        "cyclomatic_complexity": 0,
        "nesting_depth": 0,
        "repetition_ratio": 0.0
    }
    
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        # Skip header
        if len(lines) > 1:
            # Parse first data row (assuming single function per file for now)
            parts = lines[1].strip().split(",")
            if len(parts) >= 3:
                try:
                    metrics["cyclomatic_complexity"] = int(parts[0])
                    metrics["nesting_depth"] = int(parts[1])
                    metrics["repetition_ratio"] = float(parts[2])
                except (ValueError, IndexError) as e:
                    logger.warning("Error parsing CodeQL results: %s", str(e))
    
    except Exception as e:
        logger.warning("Error reading CodeQL results file: %s", str(e))
    
    return metrics

def analyze_with_tree_sitter(
    source_file: Path,
    language: str
) -> Dict[str, Any]:
    """
    Fallback analysis using tree-sitter if CodeQL is unavailable.
    
    Args:
        source_file: Path to the source file
        language: 'python' or 'java'
        
    Returns:
        Dictionary with complexity metrics
    """
    try:
        import tree_sitter
        import tree_sitter_python
        import tree_sitter_java
    except ImportError:
        logger.error("tree-sitter libraries not installed. Install with: pip install tree-sitter-python tree-sitter-java")
        return {
            "cyclomatic_complexity": 0,
            "nesting_depth": 0,
            "repetition_ratio": 0.0,
            "parse_error": True
        }
    
    try:
        # Select appropriate parser
        if language == "python":
            parser = tree_sitter.Parser()
            parser.set_language(tree_sitter_python.Language())
        elif language == "java":
            parser = tree_sitter.Parser()
            parser.set_language(tree_sitter_java.Language())
        else:
            logger.warning("Unsupported language: %s", language)
            return {
                "cyclomatic_complexity": 0,
                "nesting_depth": 0,
                "repetition_ratio": 0.0,
                "parse_error": True
            }
        
        # Read and parse source
        with open(source_file, "rb") as f:
            source_code = f.read()
        
        tree = parser.parse(source_code)
        
        # Calculate metrics from AST
        metrics = calculate_tree_sitter_metrics(tree.root_node, language)
        metrics["parse_error"] = False
        return metrics
    
    except Exception as e:
        logger.warning("tree-sitter analysis failed for %s: %s", source_file, str(e))
        return {
            "cyclomatic_complexity": 0,
            "nesting_depth": 0,
            "repetition_ratio": 0.0,
            "parse_error": True,
            "error_message": str(e)
        }

def calculate_tree_sitter_metrics(
    node: tree_sitter.Node,
    language: str,
    depth: int = 0
) -> Dict[str, Any]:
    """Recursively calculate complexity metrics from AST."""
    metrics = {
        "cyclomatic_complexity": 0,
        "nesting_depth": depth,
        "repetition_ratio": 0.0
    }
    
    # Decision points for cyclomatic complexity
    decision_nodes = {
        "python": ["if_statement", "for_statement", "while_statement", "try_statement", "except_clause"],
        "java": ["if_statement", "for_statement", "while_statement", "do_statement", "try_catch", "catch_clause"]
    }
    
    nesting_nodes = {
        "python": ["if_statement", "for_statement", "while_statement", "try_statement"],
        "java": ["if_statement", "for_statement", "while_statement", "do_statement", "try_catch"]
    }
    
    decision_types = decision_nodes.get(language, [])
    nesting_types = nesting_nodes.get(language, [])
    
    # Count decision points
    if node.type in decision_types:
        metrics["cyclomatic_complexity"] += 1
    
    # Track maximum nesting depth
    current_max_depth = depth
    if node.type in nesting_types:
        current_max_depth = max(current_max_depth, depth + 1)
    
    # Recurse into children
    total_complexity = metrics["cyclomatic_complexity"]
    max_depth = current_max_depth
    
    for child in node.children:
        child_metrics = calculate_tree_sitter_metrics(child, language, current_max_depth)
        total_complexity += child_metrics["cyclomatic_complexity"]
        max_depth = max(max_depth, child_metrics["nesting_depth"])
    
    metrics["cyclomatic_complexity"] = total_complexity
    metrics["nesting_depth"] = max_depth
    
    # Calculate repetition ratio (simplified: count repeated patterns)
    # This is a placeholder - real implementation would be more sophisticated
    if node.children:
        child_types = [child.type for child in node.children]
        type_counts = {}
        for t in child_types:
            type_counts[t] = type_counts.get(t, 0) + 1
        
        total_children = len(child_types)
        if total_children > 0:
            max_repeated = max(type_counts.values()) if type_counts else 0
            metrics["repetition_ratio"] = max_repeated / total_children
    
    return metrics

def process_single_file(
    file_path: Path,
    language: str,
    output_dir: Path
) -> Optional[Dict[str, Any]]:
    """
    Process a single code file through CodeQL and/or tree-sitter.
    
    Args:
        file_path: Path to the source file
        language: 'python' or 'java'
        output_dir: Directory for intermediate outputs
        
    Returns:
        Dictionary with file metrics or None if processing fails
    """
    logger.info("Processing file: %s (language: %s)", file_path, language)
    
    # Try CodeQL first
    codeql_metrics = run_codeql_analysis(file_path, language, output_dir)
    
    # Fallback to tree-sitter if CodeQL unavailable or failed
    if codeql_metrics is None:
        logger.info("Using tree-sitter fallback for %s", file_path)
        metrics = analyze_with_tree_sitter(file_path, language)
    else:
        metrics = codeql_metrics
    
    # Add file metadata
    metrics["file_path"] = str(file_path)
    metrics["language"] = language
    metrics["file_size_bytes"] = file_path.stat().st_size
    
    return metrics

def process_directory(
    input_dir: Path,
    output_file: Path,
    language: str
) -> int:
    """
    Process all files in a directory and write results to JSONL.
    
    Args:
        input_dir: Directory containing source files
        output_file: Output JSONL file path
        language: 'python' or 'java'
        
    Returns:
        Number of successfully processed files
    """
    logger.info("Processing directory: %s -> %s", input_dir, output_file)
    
    if not input_dir.exists():
        logger.error("Input directory does not exist: %s", input_dir)
        return 0
    
    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    processed_count = 0
    error_count = 0
    
    with open(output_file, "w", encoding="utf-8") as f:
        # Iterate through files
        for file_path in input_dir.iterdir():
            if file_path.is_file() and file_path.suffix in [".py", ".java"]:
                try:
                    metrics = process_single_file(file_path, language, input_dir.parent)
                    
                    if metrics is not None:
                        # Create CodeChunk object
                        chunk = CodeChunk(
                            file_path=str(file_path),
                            language=language,
                            cyclomatic_complexity=metrics.get("cyclomatic_complexity", 0),
                            nesting_depth=metrics.get("nesting_depth", 0),
                            repetition_ratio=metrics.get("repetition_ratio", 0.0),
                            file_size_bytes=metrics.get("file_size_bytes", 0),
                            parse_error=metrics.get("parse_error", False),
                            error_message=metrics.get("error_message", "")
                        )
                        
                        # Write to JSONL
                        f.write(json.dumps(chunk.to_dict()) + "\n")
                        processed_count += 1
                    else:
                        error_count += 1
                
                except Exception as e:
                    logger.error("Error processing %s: %s", file_path, str(e))
                    handle_parse_error(file_path, str(e))
                    error_count += 1
    
    logger.info("Completed processing %s: %d files processed, %d errors", 
               input_dir, processed_count, error_count)
    return processed_count

def main():
    """Main entry point for preprocessing."""
    logger.info("Starting preprocessing pipeline (T016)")
    
    config = get_config()
    project_root = Path(config["project_root"])
    
    # Define input/output paths
    python_train_dir = project_root / "data" / "processed" / "train_python"
    java_val_dir = project_root / "data" / "processed" / "val_java"
    
    python_output = project_root / "data" / "processed" / "annotated_python.jsonl"
    java_output = project_root / "data" / "processed" / "annotated_java.jsonl"
    
    # Check if input directories exist
    if not python_train_dir.exists():
        logger.error("Python training directory not found: %s", python_train_dir)
        sys.exit(1)
    
    if not java_val_dir.exists():
        logger.error("Java validation directory not found: %s", java_val_dir)
        sys.exit(1)
    
    # Process Python files
    python_count = process_directory(python_train_dir, python_output, "python")
    
    # Process Java files
    java_count = process_directory(java_val_dir, java_output, "java")
    
    # Summary
    total_processed = python_count + java_count
    logger.info("Preprocessing complete: %d Python files, %d Java files, total: %d",
               python_count, java_count, total_processed)
    
    if total_processed == 0:
        logger.warning("No files were processed. Check input directories and logs.")
        sys.exit(1)
    
    logger.info("Preprocessing artifacts created:")
    logger.info("  - %s", python_output)
    logger.info("  - %s", java_output)

if __name__ == "__main__":
    main()