import os
import sys
import json
import logging
import hashlib
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from utils.logging_config import setup_pipeline_logger

logger = setup_pipeline_logger("traceability_matrix")

# Configuration paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_REPORTS_DIR = PROJECT_ROOT / "data" / "reports"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
CODE_DIR = PROJECT_ROOT / "code"

def calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA-256 hash of a file."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_relative_path(file_path: Path) -> str:
    """Get path relative to project root."""
    try:
        return str(file_path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(file_path)

def extract_stats_from_json(file_path: Path) -> List[Dict[str, Any]]:
    """Extract statistics and metadata from a JSON report file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        stats = []
        # Flatten nested structures to find numeric values
        def traverse(obj, path="root"):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    traverse(v, f"{path}.{k}")
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    traverse(item, f"{path}[{i}]")
            elif isinstance(obj, (int, float)):
                stats.append({
                    "stat_path": path,
                    "value": obj,
                    "source_file": get_relative_path(file_path)
                })
        
        traverse(data)
        return stats
    except Exception as e:
        logger.warning(f"Could not extract stats from {file_path}: {e}")
        return []

def extract_stats_from_csv(file_path: Path) -> List[Dict[str, Any]]:
    """Extract statistical summaries from a CSV file."""
    try:
        df = pd.read_csv(file_path)
        stats = []
        
        # Calculate basic statistics for numeric columns
        numeric_cols = df.select_dtypes(include=['number']).columns
        
        for col in numeric_cols:
            stats.append({
                "stat_path": f"mean.{col}",
                "value": float(df[col].mean()),
                "source_file": get_relative_path(file_path)
            })
            stats.append({
                "stat_path": f"std.{col}",
                "value": float(df[col].std()),
                "source_file": get_relative_path(file_path)
            })
            stats.append({
                "stat_path": f"count.{col}",
                "value": int(df[col].count()),
                "source_file": get_relative_path(file_path)
            })
        
        return stats
    except Exception as e:
        logger.warning(f"Could not extract stats from {file_path}: {e}")
        return []

def find_code_origin(stat_value: Any, code_dir: Path) -> Optional[Dict[str, str]]:
    """
    Attempt to find the code line that produced a statistic.
    This is a heuristic search through Python files for patterns matching the statistic.
    """
    if not isinstance(stat_value, (int, float)):
        return None

    # Heuristic: Look for common aggregation patterns in code
    # This is a simplified traceability mechanism
    potential_sources = []
    
    for py_file in code_dir.rglob("*.py"):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            # Look for lines that might calculate statistics
            for i, line in enumerate(lines):
                if 'mean' in line.lower() or 'std' in line.lower() or 'count' in line.lower():
                    if 'pd.' in line or 'np.' in line or 'df.' in line:
                        potential_sources.append({
                            "file": get_relative_path(py_file),
                            "line_number": i + 1,
                            "snippet": line.strip()[:100]
                        })
                        break
        except Exception:
            continue

    # Return the most likely source (first match found in ingestion/modeling/screening)
    priority_dirs = ['ingestion', 'modeling', 'screening', 'features']
    for p_dir in priority_dirs:
        for src in potential_sources:
            if p_dir in src["file"]:
                return src
    
    if potential_sources:
        return potential_sources[0]
    
    return None

def generate_traceability_matrix() -> Dict[str, Any]:
    """
    Generate a traceability matrix linking statistics to code and data rows.
    """
    matrix = {
        "generated_at": pd.Timestamp.now().isoformat(),
        "project_root": get_relative_path(PROJECT_ROOT),
        "statistics": []
    }

    # Process JSON reports
    if DATA_REPORTS_DIR.exists():
        for json_file in DATA_REPORTS_DIR.glob("*.json"):
            logger.info(f"Processing report: {json_file.name}")
            stats = extract_stats_from_json(json_file)
            for stat in stats:
                trace_info = find_code_origin(stat['value'], CODE_DIR)
                stat['code_origin'] = trace_info
                matrix["statistics"].append(stat)

    # Process CSV data files
    if DATA_PROCESSED_DIR.exists():
        for csv_file in DATA_PROCESSED_DIR.glob("*.csv"):
            logger.info(f"Processing data: {csv_file.name}")
            stats = extract_stats_from_csv(csv_file)
            for stat in stats:
                trace_info = find_code_origin(stat['value'], CODE_DIR)
                stat['code_origin'] = trace_info
                matrix["statistics"].append(stat)

    # Add file hashes for provenance
    matrix["file_hashes"] = {}
    for directory in [DATA_PROCESSED_DIR, DATA_REPORTS_DIR]:
        if directory.exists():
            for file_path in directory.iterdir():
                if file_path.is_file():
                  key = get_relative_path(file_path)
                  try:
                      matrix["file_hashes"][key] = calculate_file_hash(file_path)
                  except Exception as e:
                      logger.warning(f"Could not hash {file_path}: {e}")

    logger.info(f"Generated traceability matrix with {len(matrix['statistics'])} statistics")
    return matrix

def save_traceability_matrix(matrix: Dict[str, Any], output_path: Path) -> None:
    """Save the traceability matrix to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(matrix, f, indent=2, default=str)
    logger.info(f"Traceability matrix saved to {get_relative_path(output_path)}")

def main():
    """Main entry point for traceability matrix generation."""
    logger.info("Starting traceability matrix generation...")
    
    try:
        matrix = generate_traceability_matrix()
        output_path = ARTIFACTS_DIR / "traceability_matrix.json"
        save_traceability_matrix(matrix, output_path)
        
        logger.info("Traceability matrix generation completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"Traceability matrix generation failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
