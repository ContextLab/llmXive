"""
Preprocessing module for code analysis.
Runs CodeQL and tree-sitter to label code chunks with complexity metrics.
"""
import json
import logging
import os
import sys
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional
import tree_sitter_python as tspython
from tree_sitter import Language, Parser

from config import get_config, get_project_root
from utils.logging import get_logger, ParseError
from utils.timeout import enforce_timeout

# Initialize logger
logger = get_logger(__name__)

# Tree-sitter constants
TREE_SITTER_LANGUAGE_PATH = Path(get_project_root()) / "data" / "tree-sitter-languages"
PYTHON_LANGUAGE = None
JAVA_LANGUAGE = None

def ensure_codeql_available() -> bool:
    """Check if CodeQL CLI is available in the system PATH."""
    try:
        result = subprocess.run(
            ["codeql", "version"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            logger.info("CodeQL CLI found.")
            return True
        else:
            logger.warning("CodeQL CLI found but returned non-zero version check.")
            return False
    except FileNotFoundError:
        logger.error("CodeQL CLI not found in PATH. Please install CodeQL CLI.")
        return False

def create_complexity_query_file(output_path: Path) -> None:
    """Create the CodeQL query file for complexity analysis."""
    query_content = """
    import python
    import java

    from Class, Method, Function, Expression, Statement, ControlFlowGraph
    select $node, $reason
    where
      $node instanceof Class or
      $node instanceof Method or
      $node instanceof Function or
      $node instanceof Expression or
      $node instanceof Statement
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(query_content)
    logger.info(f"Created CodeQL query file at {output_path}")

def run_codeql_analysis(code_path: Path, output_path: Path, language: str = "python") -> Optional[Path]:
    """Run CodeQL analysis on a code file or directory."""
    if not ensure_codeql_available():
        logger.warning("Skipping CodeQL analysis due to missing CLI.")
        return None

    db_path = Path(tempfile.mkdtemp()) / f"codeql_db_{language}"
    query_path = Path(tempfile.mkdtemp()) / "complexity.ql"

    try:
        # Create database
        logger.info(f"Creating CodeQL database for {language} at {db_path}")
        subprocess.run(
            ["codeql", "database", "create", str(db_path), f"--language={language}", f"--source-root={code_path}"],
            check=True,
            capture_output=True,
            timeout=300
        )

        # Create query file
        create_complexity_query_file(query_path)

        # Run query
        logger.info(f"Running CodeQL query on {code_path}")
        subprocess.run(
            ["codeql", "database", "analyze", str(db_path), str(query_path), "--format=csv", f"--output={output_path}"],
            check=True,
            capture_output=True,
            timeout=300
        )

        return output_path
    except subprocess.CalledProcessError as e:
        logger.error(f"CodeQL analysis failed: {e.stderr.decode() if e.stderr else str(e)}")
        return None
    except subprocess.TimeoutExpired:
        logger.error("CodeQL analysis timed out.")
        return None

def parse_codeql_results(csv_path: Path) -> List[Dict[str, Any]]:
    """Parse CodeQL CSV results into a list of dictionaries."""
    results = []
    if not csv_path.exists():
        return results

    with open(csv_path, "r", encoding="utf-8") as f:
        header = f.readline().strip().split(",")
        for line in f:
            parts = line.strip().split(",")
            if len(parts) == len(header):
                results.append(dict(zip(header, parts)))
    return results

def init_tree_sitter_languages():
    """Initialize Tree-sitter parsers for Python and Java."""
    global PYTHON_LANGUAGE, JAVA_LANGUAGE
    if PYTHON_LANGUAGE is None:
        TREE_SITTER_LANGUAGE_PATH.mkdir(parents=True, exist_ok=True)
        try:
            # Create the shared library for Python
            python_lang = Language(tspython.language())
            PYTHON_LANGUAGE = parser = Parser(python_lang)
            logger.info("Initialized Tree-sitter Python parser.")
        except Exception as e:
            logger.error(f"Failed to initialize Tree-sitter Python: {e}")
            PYTHON_LANGUAGE = None

    if JAVA_LANGUAGE is None:
        # Note: Java language support requires tree-sitter-java
        # For this implementation, we assume it's available or skip
        try:
            import tree_sitter_java as tsjava
            java_lang = Language(tsjava.language())
            JAVA_LANGUAGE = Parser(java_lang)
            logger.info("Initialized Tree-sitter Java parser.")
        except ImportError:
            logger.warning("tree-sitter-java not found. Java parsing will be skipped.")
            JAVA_LANGUAGE = None
        except Exception as e:
            logger.error(f"Failed to initialize Tree-sitter Java: {e}")
            JAVA_LANGUAGE = None

def analyze_with_tree_sitter(code: str, language: str = "python") -> Dict[str, Any]:
    """Analyze code using Tree-sitter to extract metrics."""
    init_tree_sitter_languages()
    
    if language == "python" and PYTHON_LANGUAGE is None:
        return {"error": "Python parser not available"}
    if language == "java" and JAVA_LANGUAGE is None:
        return {"error": "Java parser not available"}

    parser = PYTHON_LANGUAGE if language == "python" else JAVA_LANGUAGE
    tree = parser.parse(code.encode("utf-8"))
    
    metrics = {
        "nesting_depth": 0,
        "cyclomatic_complexity": 1,
        "function_count": 0,
        "class_count": 0
    }

    def traverse_node(node, depth=0):
        if node.type in ["if_statement", "for_statement", "while_statement", "with_statement", "try_statement"]:
            metrics["nesting_depth"] = max(metrics["nesting_depth"], depth + 1)
            metrics["cyclomatic_complexity"] += 1
        
        if node.type in ["function_definition", "method_definition"]:
            metrics["function_count"] += 1
        
        if node.type == "class_definition":
            metrics["class_count"] += 1
        
        for child in node.children:
            traverse_node(child, depth + 1 if node.type in ["if_statement", "for_statement", "while_statement", "with_statement", "try_statement"] else depth)

    traverse_node(tree.root_node)
    return metrics

def calculate_tree_sitter_metrics(code: str, language: str = "python") -> Dict[str, Any]:
    """Calculate tree-sitter metrics for a code snippet."""
    try:
        return analyze_with_tree_sitter(code, language)
    except Exception as e:
        logger.warning(f"Tree-sitter analysis failed: {e}")
        return {"error": str(e)}

def process_single_file(file_path: Path, language: str = "python") -> Dict[str, Any]:
    """Process a single code file and return metrics."""
    logger.info(f"Processing file: {file_path}")
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        
        metrics = {
            "file_path": str(file_path),
            "language": language,
            "size_bytes": len(code.encode("utf-8")),
            "line_count": len(code.splitlines()),
        }
        
        # Tree-sitter metrics
        ts_metrics = calculate_tree_sitter_metrics(code, language)
        metrics.update(ts_metrics)
        
        # CodeQL metrics (optional, if available)
        if ensure_codeql_available():
            with tempfile.NamedTemporaryFile(suffix=".ql", delete=False) as tmp:
                tmp_path = Path(tmp.name)
            try:
                output_csv = Path(tempfile.mkdtemp()) / "codeql_results.csv"
                codeql_path = run_codeql_analysis(file_path.parent, output_csv, language)
                if codeql_path:
                    codeql_results = parse_codeql_results(output_csv)
                    metrics["codeql_results"] = codeql_results
            finally:
                if tmp_path.exists():
                    tmp_path.unlink()
        
        return metrics
    except Exception as e:
        logger.error(f"Failed to process file {file_path}: {e}")
        return {
            "file_path": str(file_path),
            "language": language,
            "error": str(e)
        }

def process_directory(directory: Path, output_path: Path, language: str = "python") -> None:
    """Process all code files in a directory and write results to a JSONL file."""
    results = []
    extensions = {".py"} if language == "python" else {".java"}
    
    logger.info(f"Processing directory: {directory} for language: {language}")
    
    for root, _, files in os.walk(directory):
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                file_path = Path(root) / file
                result = process_single_file(file_path, language)
                results.append(result)
    
    # Write results to JSONL
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for result in results:
            f.write(json.dumps(result) + "\n")
    
    logger.info(f"Wrote {len(results)} results to {output_path}")

def main():
    """Main entry point for preprocessing."""
    config = get_config()
    project_root = get_project_root()
    
    # Read feasibility report to determine scope
    feasibility_path = Path(project_root) / "data" / "results" / "feasibility_report.json"
    if not feasibility_path.exists():
        logger.error("Feasibility report not found. Run T011 first.")
        sys.exit(1)
    
    with open(feasibility_path, "r") as f:
        feasibility = json.load(f)
    
    capped_n = feasibility.get("capped_N", 50)
    scope_reduction = feasibility.get("scope_reduction", {})
    include_java = not scope_reduction.get("disable_cross_language", False)
    
    # Define input directories
    python_dir = Path(project_root) / "data" / "processed" / "train_python"
    java_dir = Path(project_root) / "data" / "processed" / "val_java"
    
    # Define output files
    python_output = Path(project_root) / "data" / "processed" / "annotated_python.jsonl"
    java_output = Path(project_root) / "data" / "processed" / "annotated_java.jsonl"
    
    # Process Python
    if python_dir.exists():
        process_directory(python_dir, python_output, "python")
    else:
        logger.warning(f"Python directory not found: {python_dir}")
    
    # Process Java if enabled
    if include_java and java_dir.exists():
        process_directory(java_dir, java_output, "java")
    elif include_java:
        logger.warning(f"Java directory not found: {java_dir}")
    else:
        logger.info("Java processing disabled by scope reduction.")
    
    logger.info("Preprocessing complete.")

if __name__ == "__main__":
    main()