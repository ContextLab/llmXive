import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
import statistics

# Ensure logging is configured
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/pipeline.log')
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

class SampleSizeError(Exception):
    pass

class SignificanceError(Exception):
    pass

class DataQualityError(Exception):
    pass

def load_excluded_repos() -> List[str]:
    excluded_file = Path("data/processed/excluded_repos.txt")
    if not excluded_file.exists():
        logger.warning(f"{excluded_file} not found. Assuming no exclusions.")
        return []
    with open(excluded_file, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

def filter_excluded_repos(pr_data: List[Dict], excluded_repos: List[str]) -> List[Dict]:
    if not excluded_repos:
        return pr_data
    filtered = [pr for pr in pr_data if pr.get('repo_name') not in excluded_repos]
    removed_count = len(pr_data) - len(filtered)
    if removed_count > 0:
        logger.info(f"Filtered out {removed_count} PRs from excluded repos.")
    return filtered

def load_processed_data() -> List[Dict]:
    data_path = Path("data/processed/pr_turnaround.csv")
    if not data_path.exists():
        raise FileNotFoundError(f"Processed data file not found: {data_path}")
    
    data = []
    with open(data_path, 'r', encoding='utf-8') as f:
        # Simple CSV parsing assuming standard format
        lines = f.readlines()
        if not lines:
            return []
        
        headers = lines[0].strip().split(',')
        for line in lines[1:]:
            if not line.strip():
                continue
            values = line.strip().split(',')
            row = {}
            for i, header in enumerate(headers):
                if i < len(values):
                    val = values[i]
                    if header in ['turnaround_hours', 'stars', 'contributors']:
                        try:
                            row[header] = float(val)
                        except ValueError:
                            row[header] = 0.0
                    elif header in ['is_ai_assisted']:
                        row[header] = int(val)
                    else:
                        row[header] = val
            data.append(row)
    return data

def load_repos() -> List[Dict]:
    repos_path = Path("data/raw/repos.json")
    if not repos_path.exists():
        logger.warning(f"{repos_path} not found. Cannot load repo metadata.")
        return []
    with open(repos_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def calculate_medians(repos: List[Dict]) -> Tuple[float, float]:
    if not repos:
        return 0.0, 0.0
    stars = [r.get('stars', 0) for r in repos if r.get('stars') is not None]
    contributors = [r.get('contributors', 0) for r in repos if r.get('contributors') is not None]
    
    median_stars = statistics.median(stars) if stars else 0.0
    median_contributors = statistics.median(contributors) if contributors else 0.0
    return median_stars, median_contributors

def calculate_descriptive_statistics(data: List[Dict]) -> Dict[str, Any]:
    if not data:
        raise DataQualityError("No data provided for descriptive statistics calculation.")

    ai_times = [row['turnaround_hours'] for row in data if row.get('is_ai_assisted', 0) == 1]
    non_ai_times = [row['turnaround_hours'] for row in data if row.get('is_ai_assisted', 0) == 0]

    if not ai_times:
        raise DataQualityError("No AI-assisted PRs found in the dataset.")
    if not non_ai_times:
        raise DataQualityError("No non-AI-assisted PRs found in the dataset.")

    def calc_stats(values: List[float]) -> Dict[str, float]:
        if not values:
            return {}
        n = len(values)
        mean_val = statistics.mean(values)
        median_val = statistics.median(values)
        sd_val = statistics.stdev(values) if n > 1 else 0.0
        
        sorted_vals = sorted(values)
        q1_idx = int(n * 0.25)
        q3_idx = int(n * 0.75)
        q1 = sorted_vals[q1_idx]
        q3 = sorted_vals[q3_idx]
        
        return {
            "count": n,
            "mean": mean_val,
            "median": median_val,
            "std_dev": sd_val,
            "q1": q1,
            "q3": q3,
            "min": min(values),
            "max": max(values)
        }

    ai_stats = calc_stats(ai_times)
    non_ai_stats = calc_stats(non_ai_times)

    return {
        "ai_assisted": ai_stats,
        "non_ai_assisted": non_ai_stats
    }

def save_descriptive_statistics(stats: Dict[str, Any], output_path: str = "data/processed/descriptive_stats.json"):
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
    logger.info(f"Descriptive statistics saved to {output_path}")

def main():
    logger.info("Starting descriptive statistics calculation (T023b).")
    
    # Load excluded repos
    excluded_repos = load_excluded_repos()
    
    # Load processed data
    try:
        pr_data = load_processed_data()
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    # Filter excluded repos
    filtered_data = filter_excluded_repos(pr_data, excluded_repos)
    
    if not filtered_data:
        logger.error("No data remaining after filtering excluded repos.")
        sys.exit(1)
    
    # Calculate descriptive statistics
    try:
        stats = calculate_descriptive_statistics(filtered_data)
    except DataQualityError as e:
        logger.error(str(e))
        sys.exit(1)
    
    # Save results
    save_descriptive_statistics(stats)
    
    logger.info("Descriptive statistics calculation completed successfully.")

if __name__ == "__main__":
    main()