import os
import csv
import logging
import math
from pathlib import Path
from typing import List, Dict, Any, Tuple
import sys

# Import radon for cyclomatic complexity
try:
    from radon.complexity import cc_visit
    from radon.visitors import ComplexityError
except ImportError:
    print("Error: radon library is required. Install with: pip install radon")
    sys.exit(1)

from utils.path_normalizer import is_python_file

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_ownership_csv(file_path: Path) -> List[Dict[str, Any]]:
    """Load ownership CSV data into a list of dictionaries."""
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return []
    
    data = []
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
    except Exception as e:
        logger.error(f"Error reading CSV {file_path}: {e}")
        return []
    
    return data

def calculate_gini(values: List[float]) -> float:
    """Calculate Gini coefficient for a list of values."""
    if not values or len(values) == 0:
        return 0.0
    
    n = len(values)
    if n == 1:
        return 0.0
    
    sorted_values = sorted(values)
    cumulative = 0
    total = sum(sorted_values)
    
    if total == 0:
        return 0.0
    
    # Gini formula: G = (2 * sum(i * x_i) - (n + 1) * sum(x_i)) / (n * sum(x_i))
    numerator = 0
    for i, val in enumerate(sorted_values, 1):
        numerator += i * val
    
    gini = (2 * numerator - (n + 1) * total) / (n * total)
    return round(max(0.0, min(1.0, gini)), 3)

def get_latest_timestamp(ownership_data: List[Dict[str, Any]]) -> str:
    """Get the latest timestamp from ownership data."""
    if not ownership_data:
        return ""
    
    timestamps = [row.get('timestamp', '') for row in ownership_data if row.get('timestamp')]
    if not timestamps:
        return ""
    
    return max(timestamps)

def filter_deleted_modules(ownership_data: List[Dict[str, Any]], cutoff_timestamp: str) -> List[Dict[str, Any]]:
    """Filter out modules deleted between T and T+1."""
    # This is a placeholder for the actual logic which would require
    # comparing timestamps against a cutoff. For now, return all data.
    # In a real implementation, we would parse timestamps and filter.
    return ownership_data

def calculate_code_churn(ownership_data: List[Dict[str, Any]], module_path: str) -> int:
    """Calculate code churn (lines added + deleted) for a module."""
    churn = 0
    for row in ownership_data:
        if row.get('file_path', '').endswith(module_path):
            added = int(row.get('added', 0) or 0)
            deleted = int(row.get('deleted', 0) or 0)
            churn += added + deleted
    return churn

def calculate_module_churn_metrics(ownership_data: List[Dict[str, Any]]) -> Dict[str, int]:
    """Calculate churn metrics per module."""
    churn_metrics = {}
    for row in ownership_data:
        path = row.get('file_path', '')
        if not path:
            continue
        
        if path not in churn_metrics:
            churn_metrics[path] = 0
        
        added = int(row.get('added', 0) or 0)
        deleted = int(row.get('deleted', 0) or 0)
        churn_metrics[path] += added + deleted
    
    return churn_metrics

def process_all_ownership_files(data_dir: Path) -> Dict[str, List[Dict[str, Any]]]:
    """Process all ownership CSV files in the data directory."""
    all_data = {}
    
    for csv_file in data_dir.glob("*_ownership.csv"):
        logger.info(f"Processing {csv_file}")
        data = load_ownership_csv(csv_file)
        if data:
            all_data[csv_file.stem] = data
    
    return all_data

def save_churn_metrics_to_csv(churn_metrics: Dict[str, int], output_path: Path):
    """Save churn metrics to a CSV file."""
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['module_path', 'churn'])
        for path, churn in churn_metrics.items():
            writer.writerow([path, churn])

def calculate_cyclomatic_complexity(repo_path: Path, module_path: str) -> Tuple[int, bool]:
    """
    Calculate cyclomatic complexity for a single Python file using radon.
    
    Returns:
        Tuple of (total_complexity, is_valid)
        is_valid is True if the file was successfully parsed and has valid scores.
    """
    full_path = repo_path / module_path
    
    if not full_path.exists():
        return 0, False
    
    if not is_python_file(str(module_path)):
        return 0, False
    
    try:
        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
            source_code = f.read()
        
        # Visit the source code to get complexity results
        results = cc_visit(source_code)
        
        if not results:
            # File parsed but no complexity info (e.g., empty file)
            # Consider this valid but with 0 complexity
            return 0, True
        
        # Sum up complexity for all functions/classes in the file
        total_complexity = sum(r.complexity for r in results)
        return total_complexity, True
        
    except Exception as e:
        logger.warning(f"Failed to calculate complexity for {full_path}: {e}")
        return 0, False

def compute_cyclomatic_complexity_for_repos(
    repos_dir: Path, 
    ownership_data: Dict[str, List[Dict[str, Any]]],
    output_path: Path
) -> Dict[str, Any]:
    """
    Compute cyclomatic complexity for all Python modules across repositories.
    
    This function:
    1. Iterates through all repositories in repos_dir
    2. For each repo, identifies Python modules from ownership data
    3. Calculates complexity using radon
    4. Validates that >= 95% of Python modules have valid scores
    5. Saves results to output_path
    
    Args:
        repos_dir: Path to directory containing cloned repositories
        ownership_data: Dictionary mapping repo names to ownership CSV data
        output_path: Path to save the complexity results CSV
    
    Returns:
        Dictionary with statistics about the computation
    """
    results = []
    total_python_modules = 0
    valid_complexity_count = 0
    invalid_files = []
    
    logger.info(f"Starting cyclomatic complexity calculation for {len(ownership_data)} repositories")
    
    for repo_name, data in ownership_data.items():
        repo_path = repos_dir / repo_name
        
        if not repo_path.exists():
            logger.warning(f"Repository directory not found: {repo_path}")
            continue
        
        # Extract unique file paths from ownership data for this repo
        file_paths = set()
        for row in data:
            file_path = row.get('file_path', '')
            if file_path and is_python_file(file_path):
                file_paths.add(file_path)
        
        logger.info(f"Processing {len(file_paths)} Python files in {repo_name}")
        
        for module_path in file_paths:
            total_python_modules += 1
            complexity, is_valid = calculate_cyclomatic_complexity(repo_path, module_path)
            
            if is_valid:
                valid_complexity_count += 1
            
            results.append({
                'repo': repo_name,
                'module_path': module_path,
                'complexity': complexity,
                'is_valid': is_valid
            })
            
            if not is_valid:
                invalid_files.append(f"{repo_name}/{module_path}")
    
    # Verification: Check if valid_count / total_count >= 0.95
    if total_python_modules > 0:
        validity_ratio = valid_complexity_count / total_python_modules
        logger.info(f"Complexity calculation validity: {validity_ratio:.2%} ({valid_complexity_count}/{total_python_modules})")
        
        if validity_ratio < 0.95:
            logger.critical(f"CRITICAL: Valid complexity ratio {validity_ratio:.2%} is below 95% threshold!")
            logger.critical(f"Invalid files: {invalid_files[:10]}...")  # Show first 10
            # We do not raise an exception here to allow partial results, 
            # but we log the critical failure as required.
        else:
            logger.info("Complexity calculation passed 95% validity threshold.")
    else:
        logger.warning("No Python modules found to analyze.")
    
    # Save results to CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['repo', 'module_path', 'complexity', 'is_valid'])
        writer.writeheader()
        writer.writerows(results)
    
    return {
        'total_python_modules': total_python_modules,
        'valid_complexity_count': valid_complexity_count,
        'validity_ratio': valid_complexity_count / total_python_modules if total_python_modules > 0 else 0,
        'output_file': str(output_path)
    }

def main():
    """Main entry point for metrics calculation."""
    # Configuration
    repos_dir = Path("data/raw")
    ownership_dir = Path("data/intermediate")
    output_file = Path("data/results/cyclomatic_complexity.csv")
    
    logger.info("Starting cyclomatic complexity calculation")
    
    # Load ownership data
    if not ownership_dir.exists():
        logger.error(f"Ownership directory not found: {ownership_dir}")
        return
    
    ownership_data = process_all_ownership_files(ownership_dir)
    
    if not ownership_data:
        logger.warning("No ownership data found to process.")
        return
    
    # Calculate complexity
    stats = compute_cyclomatic_complexity_for_repos(repos_dir, ownership_data, output_file)
    
    logger.info(f"Complexity calculation complete. Results saved to {output_file}")
    logger.info(f"Statistics: {stats}")

if __name__ == "__main__":
    main()