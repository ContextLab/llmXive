"""
Main data collection pipeline for NPM dependencies analysis.
Orchestrates clients, handles missing repos, and exports results.
"""
import argparse
import json
import logging
import sys
import csv
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import from existing API surface
from src.services.npm_client import NpmClient
from src.services.github_client import GithubClient
from src.services.audit_client import AuditClient
from src.services.dependency_resolver import DependencyResolver
from src.utils.age import calculate_age_in_days
from src.utils.cache import save_response_to_cache, load_from_cache
from src.config.settings import get_config

logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description="Collect NPM dependency data")
    parser.add_argument("--top-packages", type=int, default=None,
                        help="Number of top packages to fetch (overrides env)")
    parser.add_argument("--export", action="store_true",
                        help="Export data to CSV and JSON")
    parser.add_argument("--metrics", action="store_true",
                        help="Calculate and export metrics")
    parser.add_argument("--output-csv", type=str, default="data/processed/dependencies_raw.csv",
                        help="Output CSV path")
    parser.add_argument("--output-metrics", type=str, default="data/processed/metrics.json",
                        help="Output metrics JSON path")
    return parser.parse_args()

def fetch_top_packages(n: int) -> List[Dict[str, Any]]:
    """Fetch top N packages by weekly downloads."""
    client = NpmClient()
    logger.info(f"Fetching top {n} packages from NPM...")
    packages = client.get_top_packages(n)
    logger.info(f"Fetched {len(packages)} packages")
    return packages

def process_package(pkg_name: str, resolver: DependencyResolver) -> Dict[str, Any]:
    """Process a single package: resolve deps, fetch metadata, calculate ages."""
    try:
        # Resolve dependencies (direct + transitive)
        deps = resolver.resolve_dependencies(pkg_name)
        if not deps:
            logger.warning(f"No dependencies found for {pkg_name}")
            return {"name": pkg_name, "version": None, "dependencies": [], "error": "No deps"}

        results = []
        for dep in deps:
            dep_name = dep.get("name")
            if not dep_name:
                continue

            # Fetch GitHub metadata for age calculation
            github_data = resolver.fetch_github_metadata(dep_name)
            last_release = github_data.get("last_release_date") if github_data else None
            last_commit = github_data.get("last_commit_date") if github_data else None

            # Calculate age (fail loudly if logic is wrong, but handle nulls per FR-010)
            age_days = calculate_age_in_days(last_release)

            # Fetch audit data for vulnerability count
            audit_data = resolver.fetch_audit_data(dep_name)
            vuln_count = audit_data.get("vulnerability_count", 0) if audit_data else 0

            results.append({
                "name": dep_name,
                "version": dep.get("version", "unknown"),
                "age_in_days": age_days,
                "vulnerability_count": vuln_count,
                "last_release_date": last_release,
                "last_commit_date": last_commit,
                "has_release_metadata": last_release is not None
            })

        return {
            "name": pkg_name,
            "version": deps[0].get("package_version") if deps else None,
            "dependencies": results,
            "error": None
        }
    except Exception as e:
        logger.error(f"Error processing {pkg_name}: {e}")
        return {"name": pkg_name, "version": None, "dependencies": [], "error": str(e)}

def run_data_collection(top_n: int) -> List[Dict[str, Any]]:
    """Run the full collection pipeline."""
    config = get_config()
    resolver = DependencyResolver()
    all_results = []

    packages = fetch_top_packages(top_n)

    for i, pkg in enumerate(packages):
        pkg_name = pkg.get("name")
        if not pkg_name:
            continue

        logger.info(f"Processing [{i+1}/{top_n}]: {pkg_name}")
        result = process_package(pkg_name, resolver)
        all_results.append(result)

        # Optional: Add rate limiting delay if needed
        # time.sleep(0.1)

    return all_results

def export_to_csv(data: List[Dict[str, Any]], output_path: str) -> None:
    """Export flattened dependency data to CSV."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for pkg in data:
        pkg_name = pkg.get("name")
        for dep in pkg.get("dependencies", []):
            dep["package_source"] = pkg_name
            rows.append(dep)

    if not rows:
        logger.warning("No data to export to CSV")
        return

    fieldnames = ["package_source", "name", "version", "age_in_days", "vulnerability_count",
                  "last_release_date", "last_commit_date", "has_release_metadata"]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    logger.info(f"Exported {len(rows)} rows to {output_path}")

def calculate_and_export_metrics(data: List[Dict[str, Any]], output_path: str) -> None:
    """Calculate metrics and export to JSON."""
    total_deps = 0
    missing_release = 0

    for pkg in data:
        deps = pkg.get("dependencies", [])
        total_deps += len(deps)
        for dep in deps:
            if not dep.get("has_release_metadata"):
                missing_release += 1

    metrics = {
        "total_dependencies": total_deps,
        "missing_release_metadata_count": missing_release,
        "missing_release_metadata_ratio": missing_release / total_deps if total_deps > 0 else 0.0,
        "timestamp": datetime.utcnow().isoformat()
    }

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Exported metrics to {output_path}")

def main():
    args = parse_args()

    # Setup logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    # Determine top packages count
    top_n = args.top_packages
    if top_n is None:
        top_n = int(os.getenv("TOP_PACKAGES", "100"))
        logger.info(f"Using default TOP_PACKAGES from env: {top_n}")

    # Ensure output directories exist
    Path("data/processed").mkdir(parents=True, exist_ok=True)

    # Run collection
    logger.info(f"Starting data collection for top {top_n} packages...")
    data = run_data_collection(top_n)

    if not data:
        logger.error("Data collection returned empty results. Failing loudly.")
        sys.exit(1)

    # Export if requested
    if args.export:
        export_to_csv(data, args.output_csv)
        if not os.path.exists(args.output_csv):
            logger.error(f"Failed to create {args.output_csv}. Failing loudly.")
            sys.exit(1)

    # Metrics if requested
    if args.metrics:
        calculate_and_export_metrics(data, args.output_metrics)
        if not os.path.exists(args.output_metrics):
            logger.error(f"Failed to create {args.output_metrics}. Failing loudly.")
            sys.exit(1)

    logger.info("Data collection and export completed successfully.")

if __name__ == "__main__":
    main()