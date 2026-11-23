"""
Metric Extraction Module (US2)

Extracts static analysis metrics from code snippets using radon and pylint.
Implements:
- Radon: Cyclomatic complexity, LOC, Maintainability Index
- Pylint: Bug indicators, style issues

Outputs metrics to CSV files in data/metrics/
"""
import os
import sys
import logging
import ast
import tempfile
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime

# Radon imports
try:
    from radon.complexity import cc_visit
    from radon.raw import analyze as radon_raw_analyze
    from radon.mi import mi_visit
    RADON_AVAILABLE = True
except ImportError:
    RADON_AVAILABLE = False
    # Import stubs to allow module load for error reporting
    cc_visit = None
    radon_raw_analyze = None
    mi_visit = None

# Pylint imports
try:
    from pylint.lint import Run
    from pylint.reporters.text import TextReporter
    from io import StringIO
    PYLINT_AVAILABLE = True
except ImportError:
    PYLINT_AVAILABLE = False
    Run = None
    TextReporter = None
    StringIO = None

from data_model import MetricResult, validate_metric_result
from logging_config import setup_logger, get_logger

# Constants
METRICS_OUTPUT_DIR = Path("data/metrics")
LOG_FILE = "data/metrics/extraction.log"

@dataclass
class RadonMetrics:
    """Container for radon-derived metrics."""
    snippet_id: str
    cyclomatic_complexity: float
    loc: int
    maintainability_index: float
    source: str = "radon"
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

@dataclass
class PylintMetrics:
    """Container for pylint-derived metrics."""
    snippet_id: str
    bug_count: int
    style_issues: int
    error_count: int
    warning_count: int
    message_count: int
    source: str = "pylint"
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

def setup_extraction_logger(name: str = "metric_extraction", log_file: Optional[str] = None) -> logging.Logger:
    """Set up a standard logging.Logger for metric extraction."""
    if log_file is None:
        log_file = LOG_FILE
    
    # Ensure output directory exists
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers
    if not logger.handlers:
        # File handler
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.INFO)
        fh.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(fh)
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(logging.Formatter(
            '%(levelname)s: %(message)s'
        ))
        logger.addHandler(ch)
    
    return logger

def extract_radon_metrics(snippet_id: str, code: str) -> Optional[Dict[str, Any]]:
    """
    Extract radon metrics from a code snippet.
    
    Args:
        snippet_id: Unique identifier for the snippet
        code: Python code string
        
    Returns:
        Dictionary with metrics or None if extraction fails
    """
    if not RADON_AVAILABLE:
        logging.error("Radon library not installed. Cannot extract metrics.")
        return None
    
    try:
        # Cyclomatic complexity
        complexity_results = cc_visit(code)
        total_complexity = sum(r.complexity for r in complexity_results)
        
        # Raw metrics (LOC, etc.)
        raw_metrics = radon_raw_analyze(code)
        loc = raw_metrics.loc
        
        # Maintainability Index
        # mi_visit returns a list of MI values for each module
        # We pass False to get the raw MI value (not normalized)
        mi_results = mi_visit(code, False)
        mi_value = mi_results[0] if mi_results else 0.0
        
        return {
            "snippet_id": snippet_id,
            "cyclomatic_complexity": total_complexity,
            "loc": loc,
            "maintainability_index": mi_value,
            "source": "radon",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logging.error(f"Error extracting radon metrics for snippet {snippet_id}: {e}")
        return None

def extract_pylint_metrics(snippet_id: str, code: str) -> Optional[Dict[str, Any]]:
    """
    Extract pylint metrics from a code snippet.
    
    Args:
        snippet_id: Unique identifier for the snippet
        code: Python code string
        
    Returns:
        Dictionary with metrics or None if extraction fails
    """
    if not PYLINT_AVAILABLE:
        logging.error("Pylint library not installed. Cannot extract metrics.")
        return None
    
    try:
        # Create a temporary file for pylint to analyze
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_path = f.name
        
        # Capture pylint output
        output_buffer = StringIO()
        reporter = TextReporter(output_buffer)
        
        # Run pylint with specific checks enabled
        # Disable some checks to speed up processing
        Run(
            [temp_path, 
             '--disable=C0114,C0115,C0116',  # Disable missing docstring checks
             '--reports=no',
             '--score=no'],
            reporter=reporter,
            exit=False
        )
        
        # Parse output
        output = output_buffer.getvalue()
        
        # Count message types
        bug_count = 0
        style_issues = 0
        error_count = 0
        warning_count = 0
        message_count = 0
        
        for line in output.split('\n'):
            if not line.strip():
                continue
            
            message_count += 1
            
            if ':E' in line or ':F' in line:  # Error or Fatal
                error_count += 1
                if 'unreachable' in line or 'no-member' in line:
                    bug_count += 1
            elif ':W' in line:  # Warning
                warning_count += 1
                if 'style' in line.lower() or 'convention' in line.lower():
                    style_issues += 1
            elif ':C' in line:  # Convention
                if 'style' in line.lower():
                    style_issues += 1
        
        return {
            "snippet_id": snippet_id,
            "bug_count": bug_count,
            "style_issues": style_issues,
            "error_count": error_count,
            "warning_count": warning_count,
            "message_count": message_count,
            "source": "pylint",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logging.error(f"Error extracting pylint metrics for snippet {snippet_id}: {e}")
        return None
    finally:
        # Clean up temporary file
        try:
            os.unlink(temp_path)
        except OSError:
            pass

def process_snippets_for_metrics(
    snippets: List[Dict[str, Any]],
    logger: Optional[logging.Logger] = None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Process a list of snippets and extract metrics.
    
    Args:
        snippets: List of snippet dictionaries with 'id' and 'code' keys
        logger: Logger instance (optional)
        
    Returns:
        Tuple of (radon_metrics, pylint_metrics) lists
    """
    if logger is None:
        logger = setup_extraction_logger()
    
    radon_metrics = []
    pylint_metrics = []
    
    total = len(snippets)
    for i, snippet in enumerate(snippets):
        snippet_id = snippet.get('id')
        code = snippet.get('code')
        
        if not snippet_id or not code:
            logger.warning(f"Skipping snippet {i}: missing id or code")
            continue
        
        # Extract radon metrics
        radon_result = extract_radon_metrics(snippet_id, code)
        if radon_result:
            radon_metrics.append(radon_result)
        
        # Extract pylint metrics
        pylint_result = extract_pylint_metrics(snippet_id, code)
        if pylint_result:
            pylint_metrics.append(pylint_result)
        
        if (i + 1) % 100 == 0:
            logger.info(f"Processed {i + 1}/{total} snippets")
    
    logger.info(f"Completed metric extraction: {len(radon_metrics)} radon, {len(pylint_metrics)} pylint")
    return radon_metrics, pylint_metrics

def write_metrics_to_csv(
    metrics: List[Dict[str, Any]],
    output_path: Path,
    metric_type: str
) -> None:
    """
    Write metrics to a CSV file.
    
    Args:
        metrics: List of metric dictionaries
        output_path: Path to output CSV file
        metric_type: Type of metric (e.g., 'radon', 'pylint')
    """
    import pandas as pd
    
    if not metrics:
        logger = setup_extraction_logger()
        logger.warning(f"No metrics to write for {metric_type}")
        # Write empty file with headers
        df = pd.DataFrame()
        df.to_csv(output_path, index=False)
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(metrics)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to CSV
    df.to_csv(output_path, index=False)
    
    logger = setup_extraction_logger()
    logger.info(f"Wrote {len(metrics)} {metric_type} metrics to {output_path}")

def run_metric_extraction(
    input_file: Optional[Path] = None,
    snippets: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, str]:
    """
    Main entry point for metric extraction.
    
    Args:
        input_file: Optional path to JSON file containing snippets
        snippets: Optional list of snippets (overrides input_file)
        
    Returns:
        Dictionary mapping metric types to output file paths
    """
    logger = setup_extraction_logger()
    logger.info("Starting metric extraction pipeline")
    
    # Load snippets if not provided
    if snippets is None:
        if input_file is None:
            # Default input file
            input_file = Path("data/processed/filtered_snippets.json")
        
        if not input_file.exists():
            logger.error(f"Input file not found: {input_file}")
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        with open(input_file, 'r') as f:
            data = json.load(f)
            snippets = data.get('snippets', [])
    
    logger.info(f"Loaded {len(snippets)} snippets for metric extraction")
    
    # Extract metrics
    radon_metrics, pylint_metrics = process_snippets_for_metrics(snippets, logger)
    
    # Write results
    radon_output = METRICS_OUTPUT_DIR / "radon_metrics.csv"
    pylint_output = METRICS_OUTPUT_DIR / "pylint_metrics.csv"
    
    write_metrics_to_csv(radon_metrics, radon_output, "radon")
    write_metrics_to_csv(pylint_metrics, pylint_output, "pylint")
    
    result = {
        "radon": str(radon_output),
        "pylint": str(pylint_output)
    }
    
    logger.info(f"Metric extraction complete. Results: {result}")
    return result

def main():
    """Main entry point for command-line execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract metrics from code snippets")
    parser.add_argument(
        "--input", 
        type=Path, 
        default=Path("data/processed/filtered_snippets.json"),
        help="Input JSON file containing snippets"
    )
    args = parser.parse_args()
    
    if not args.input.exists():
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    
    try:
        result = run_metric_extraction(input_file=args.input)
        print(f"Metric extraction complete. Output files: {result}")
    except Exception as e:
        print(f"Error during metric extraction: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()