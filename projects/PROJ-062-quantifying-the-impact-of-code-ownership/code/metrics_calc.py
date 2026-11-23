import os
import csv
import logging
import math
from pathlib import Path
from typing import List, Dict, Any, Tuple
from datetime import datetime
from dateutil.relativedelta import relativedelta

# Local imports
from config import get_cutoff_date, get_output_dir, get_repo_list
from utils.logging_utils import get_logger
from utils.path_normalizer import normalize_path

logger = get_logger(__name__)

def load_ownership_csv(repo_name: str) -> List[Dict[str, Any]]:
    """Load ownership CSV for a specific repository."""
    output_dir = get_output_dir()
    ownership_path = Path(output_dir) / "ownership_metrics" / f"{repo_name}_ownership.csv"
    
    if not ownership_path.exists():
        logger.warning(f"Ownership file not found: {ownership_path}")
        return []
    
    data = []
    with open(ownership_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data

def calculate_gini(values: List[float]) -> float:
    """Calculate Gini coefficient for a list of values."""
    if not values or len(values) == 0:
        return 0.0
    
    values = sorted(values)
    n = len(values)
    if n == 1:
        return 0.0
    
    index = list(range(1, n + 1))
    total = sum(values)
    if total == 0:
        return 0.0
    
    gini = (sum((2 * i - n - 1) * v for i, v in zip(index, values))) / (n * total)
    return max(0.0, min(1.0, gini))

def get_latest_timestamp(repo_name: str) -> datetime:
    """Get the latest commit timestamp for a repository."""
    commits_path = Path(get_output_dir()) / "intermediate" / f"{repo_name}_commits.csv"
    if not commits_path.exists():
        return datetime.now()
    
    latest = datetime.min
    with open(commits_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                ts = datetime.fromisoformat(row['timestamp'])
                if ts > latest:
                    latest = ts
            except (ValueError, KeyError):
                continue
    return latest

def filter_deleted_modules(
    module_data: List[Dict[str, Any]],
    repo_name: str
) -> List[Dict[str, Any]]:
    """Filter out modules deleted between T and T+1."""
    cutoff = get_cutoff_date()
    cutoff_plus_one = cutoff + relativedelta(months=1)
    
    filtered = []
    for module in module_data:
        # Check if module has data in both periods
        # Implementation depends on specific data structure
        # For now, return all (filtering logic is in T020)
        filtered.append(module)
    
    return filtered

def calculate_code_churn(repo_name: str) -> Dict[str, int]:
    """Calculate code churn (lines added/deleted) for a repository."""
    churn_path = Path(get_output_dir()) / "intermediate" / f"{repo_name}_churn.csv"
    if not churn_path.exists():
        return {"added": 0, "deleted": 0}
    
    added = 0
    deleted = 0
    with open(churn_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                added += int(row.get('lines_added', 0))
                deleted += int(row.get('lines_deleted', 0))
            except ValueError:
                continue
    
    return {"added": added, "deleted": deleted}

def calculate_module_churn_metrics(repo_name: str) -> Dict[str, Dict[str, int]]:
    """Calculate churn metrics per module."""
    churn_path = Path(get_output_dir()) / "intermediate" / f"{repo_name}_churn.csv"
    if not churn_path.exists():
        return {}
    
    module_churn = {}
    with open(churn_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            module_path = row.get('file_path', '')
            if module_path not in module_churn:
                module_churn[module_path] = {"added": 0, "deleted": 0}
            
            try:
                module_churn[module_path]["added"] += int(row.get('lines_added', 0))
                module_churn[module_path]["deleted"] += int(row.get('lines_deleted', 0))
            except ValueError:
                continue
    
    return module_churn

def process_all_ownership_files() -> Dict[str, List[Dict[str, Any]]]:
    """Process all ownership CSV files and return data by repository."""
    output_dir = get_output_dir()
    ownership_dir = Path(output_dir) / "ownership_metrics"
    
    if not ownership_dir.exists():
        logger.warning(f"Ownership metrics directory not found: {ownership_dir}")
        return {}
    
    all_data = {}
    for csv_file in ownership_dir.glob("*_ownership.csv"):
        repo_name = csv_file.stem.replace("_ownership", "")
        data = load_ownership_csv(repo_name)
        if data:
            all_data[repo_name] = data
    
    return all_data

def save_churn_metrics_to_csv(repo_name: str, churn_data: Dict[str, Dict[str, int]]) -> None:
    """Save churn metrics to CSV."""
    output_dir = get_output_dir()
    churn_path = Path(output_dir) / "results" / f"{repo_name}_churn_metrics.csv"
    
    with open(churn_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['module_path', 'lines_added', 'lines_deleted'])
        writer.writeheader()
        
        for module_path, metrics in churn_data.items():
            writer.writerow({
                'module_path': module_path,
                'lines_added': metrics['added'],
                'lines_deleted': metrics['deleted']
            })

def calculate_cyclomatic_complexity(repo_name: str) -> Dict[str, float]:
    """Calculate cyclomatic complexity for Python files in a repository."""
    from radon.complexity import cc_visit
    from radon.visitors import ComplexityVisitor
    
    repo_path = Path(get_output_dir()) / "raw" / repo_name
    if not repo_path.exists():
        return {}
    
    complexity_data = {}
    
    for py_file in repo_path.rglob("*.py"):
        try:
            with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                source = f.read()
            
            results = cc_visit(source)
            total_complexity = sum(block.complexity for block in results)
            
            relative_path = py_file.relative_to(repo_path)
            complexity_data[str(relative_path)] = total_complexity
        except Exception as e:
            logger.warning(f"Error processing {py_file}: {e}")
            continue
    
    return complexity_data

def compute_cyclomatic_complexity_for_repos() -> Dict[str, Dict[str, float]]:
    """Compute cyclomatic complexity for all repositories."""
    all_complexity = {}
    repo_list = get_repo_list()
    
    for repo_name in repo_list:
        complexity = calculate_cyclomatic_complexity(repo_name)
        if complexity:
            all_complexity[repo_name] = complexity
    
    return all_complexity

def calculate_bug_density(repo_name: str) -> Dict[str, float]:
    """Calculate bug density (bugs/KLOC) for a repository."""
    issues_path = Path(get_output_dir()) / "intermediate" / f"{repo_name}_issues.csv"
    churn_path = Path(get_output_dir()) / "intermediate" / f"{repo_name}_churn.csv"
    
    if not issues_path.exists() or not churn_path.exists():
        return {}
    
    # Count issues per module
    issue_counts = {}
    with open(issues_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            module_path = row.get('file_path', '')
            if module_path not in issue_counts:
                issue_counts[module_path] = 0
            issue_counts[module_path] += 1
    
    # Calculate lines of code per module
    module_lines = {}
    with open(churn_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            module_path = row.get('file_path', '')
            if module_path not in module_lines:
                module_lines[module_path] = 0
            try:
                module_lines[module_path] += int(row.get('lines_added', 0))
            except ValueError:
                continue
    
    # Calculate bug density
    bug_density = {}
    for module_path, lines in module_lines.items():
        if lines > 0:
            kloc = lines / 1000.0
            bugs = issue_counts.get(module_path, 0)
            bug_density[module_path] = bugs / kloc if kloc > 0 else 0.0
    
    return bug_density

def save_bug_density_metrics(repo_name: str, bug_density: Dict[str, float]) -> None:
    """Save bug density metrics to CSV."""
    output_dir = get_output_dir()
    density_path = Path(output_dir) / "results" / f"{repo_name}_bug_density.csv"
    
    with open(density_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['module_path', 'bug_density'])
        writer.writeheader()
        
        for module_path, density in bug_density.items():
            writer.writerow({
                'module_path': module_path,
                'bug_density': round(density, 4)
            })

def calculate_module_size_and_age(repo_name: str) -> Tuple[Dict[str, float], Dict[str, float]]:
    """
    Calculate module Size (KLOC) and Age (months since creation).
    Also generates Gini² (Gini squared) for each module.
    
    Returns:
        Tuple of (size_dict, age_dict) where:
        - size_dict: {module_path: size_in_kloc}
        - age_dict: {module_path: age_in_months}
    """
    # Load ownership data
    ownership_data = load_ownership_csv(repo_name)
    if not ownership_data:
        logger.warning(f"No ownership data for {repo_name}")
        return {}, {}
    
    # Get commit history to determine file creation dates
    commits_path = Path(get_output_dir()) / "intermediate" / f"{repo_name}_commits.csv"
    if not commits_path.exists():
        logger.warning(f"Commit history not found for {repo_name}")
        return {}, {}
    
    # Parse commit history to find first appearance of each file
    file_first_commit = {}
    cutoff = get_cutoff_date()
    
    with open(commits_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            file_path = row.get('file_path', '')
            timestamp_str = row.get('timestamp', '')
            
            try:
                timestamp = datetime.fromisoformat(timestamp_str)
                # Only consider commits before cutoff date
                if timestamp <= cutoff:
                    if file_path not in file_first_commit:
                        file_first_commit[file_path] = timestamp
                    else:
                        if timestamp < file_first_commit[file_path]:
                            file_first_commit[file_path] = timestamp
            except (ValueError, KeyError):
                continue
    
    # Calculate size (KLOC) per module
    # We'll use the last known line count from churn data
    churn_path = Path(get_output_dir()) / "intermediate" / f"{repo_name}_churn.csv"
    module_lines = {}
    
    if churn_path.exists():
        with open(churn_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                module_path = row.get('file_path', '')
                try:
                    lines = int(row.get('lines_added', 0)) - int(row.get('lines_deleted', 0))
                    if module_path not in module_lines:
                        module_lines[module_path] = 0
                    module_lines[module_path] += lines
                except ValueError:
                    continue
    
    # If no churn data, estimate size from ownership data
    if not module_lines:
        for row in ownership_data:
            module_path = row.get('file_path', '')
            if module_path not in module_lines:
                module_lines[module_path] = 0
            # Use a simple heuristic: count occurrences as proxy for size
            module_lines[module_path] += 1
    
    # Convert to KLOC
    size_dict = {}
    for module_path, lines in module_lines.items():
        kloc = max(0.0, lines / 1000.0)
        size_dict[module_path] = kloc
    
    # Calculate Age (months since creation)
    age_dict = {}
    latest_ts = get_latest_timestamp(repo_name)
    
    for module_path, first_commit in file_first_commit.items():
        delta = latest_ts - first_commit
        age_months = delta.days / 30.44  # Average days per month
        age_dict[module_path] = age_months
    
    # Calculate Gini² for each module (using ownership data)
    # Group ownership by module and calculate Gini
    module_ownership = {}
    for row in ownership_data:
        module_path = row.get('file_path', '')
        committer = row.get('committer', '')
        commits = int(row.get('commits', 0))
        
        if module_path not in module_ownership:
            module_ownership[module_path] = {}
        
        if committer not in module_ownership[module_path]:
            module_ownership[module_path][committer] = 0
        module_ownership[module_path][committer] += commits
    
    # Store Gini² in a separate dict for T031
    ginisq_dict = {}
    for module_path, committers in module_ownership.items():
        if committers:
            values = list(committers.values())
            gini = calculate_gini(values)
            ginisq_dict[module_path] = gini * gini
    
    return size_dict, age_dict, ginisq_dict

def save_size_age_metrics(repo_name: str, size_dict: Dict[str, float], age_dict: Dict[str, float], ginisq_dict: Dict[str, float]) -> None:
    """Save Size, Age, and Gini² metrics to CSV."""
    output_dir = get_output_dir()
    metrics_path = Path(output_dir) / "results" / f"{repo_name}_size_age_ginisq.csv"
    
    with open(metrics_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(
            f, 
            fieldnames=['module_path', 'size_kloc', 'age_months', 'gini_squared']
        )
        writer.writeheader()
        
        # Use union of all keys
        all_modules = set(size_dict.keys()) | set(age_dict.keys()) | set(ginisq_dict.keys())
        
        for module_path in all_modules:
            writer.writerow({
                'module_path': module_path,
                'size_kloc': round(size_dict.get(module_path, 0.0), 4),
                'age_months': round(age_dict.get(module_path, 0.0), 2),
                'gini_squared': round(ginisq_dict.get(module_path, 0.0), 6)
            })

def process_all_ownership_for_size_age() -> Dict[str, Dict[str, Any]]:
    """
    Process all repositories to calculate Size, Age, and Gini².
    Returns a dictionary with results for each repository.
    """
    repo_list = get_repo_list()
    results = {}
    
    for repo_name in repo_list:
        logger.info(f"Processing size, age, and Gini² for {repo_name}")
        
        try:
            size_dict, age_dict, ginisq_dict = calculate_module_size_and_age(repo_name)
            
            if size_dict or age_dict:
                save_size_age_metrics(repo_name, size_dict, age_dict, ginisq_dict)
                
                results[repo_name] = {
                    'size': size_dict,
                    'age': age_dict,
                    'gini_squared': ginisq_dict,
                    'module_count': len(size_dict)
                }
                logger.info(f"Completed {repo_name}: {len(size_dict)} modules processed")
            else:
                logger.warning(f"No valid data for {repo_name}")
                
        except Exception as e:
            logger.error(f"Error processing {repo_name}: {e}", exc_info=True)
            continue
    
    return results

def main():
    """Main entry point for Size, Age, and Gini² calculation."""
    logger.info("Starting Size, Age, and Gini² calculation")
    
    results = process_all_ownership_for_size_age()
    
    if results:
        total_modules = sum(r['module_count'] for r in results.values())
        logger.info(f"Successfully processed {len(results)} repositories with {total_modules} total modules")
        
        # Print summary
        for repo_name, data in results.items():
            logger.info(f"  {repo_name}: {data['module_count']} modules")
            if data['size']:
                avg_size = sum(data['size'].values()) / len(data['size'])
                logger.info(f"    Average size: {avg_size:.3f} KLOC")
            if data['age']:
                avg_age = sum(data['age'].values()) / len(data['age'])
                logger.info(f"    Average age: {avg_age:.2f} months")
    else:
        logger.warning("No repositories processed successfully")
    
    return results

if __name__ == "__main__":
    main()