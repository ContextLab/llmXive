"""
Data Collection Pipeline for NPM Dependency Analysis.

This module orchestrates the collection of dependency data from NPM and GitHub APIs.
It handles:
- Fetching top N packages by weekly downloads
- Resolving dependency trees (direct and transitive)
- Fetching maintenance metadata (last commit, last release)
- Fetching vulnerability counts via npm audit
- Handling missing repositories (null dates)
- Skipping private packages
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Import from project modules
from src.services.npm_client import NpmClient
from src.services.github_client import GithubClient
from src.services.audit_client import AuditClient
from src.services.dependency_resolver import DependencyResolver
from src.models.data_models import Dependency, Package
from src.config.settings import get_config
from src.utils.cache_manager import CacheManager
from src.utils.checksum import generate_checksum

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def collect_data(
    top_n: int = 100,
    output_dir: Optional[str] = None,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Main data collection pipeline.

    Args:
        top_n: Number of top packages to analyze (default: 100)
        output_dir: Directory to save collected data (default: data/processed)
        dry_run: If True, only collect metadata without fetching full data

    Returns:
        Dictionary containing collection statistics and paths to output files
    """
    config = get_config()
    cache_manager = CacheManager()

    # Setup output directory
    if output_dir is None:
        output_dir = str(Path(config.project_root) / "data" / "processed")
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting data collection for top {top_n} packages")
    logger.info(f"Output directory: {output_dir}")

    # Initialize clients
    npm_client = NpmClient(config)
    github_client = GithubClient(config)
    audit_client = AuditClient(config)
    resolver = DependencyResolver(npm_client, github_client, audit_client, cache_manager)

    # Statistics tracking
    stats = {
        "start_time": datetime.now().isoformat(),
        "top_n": top_n,
        "packages_processed": 0,
        "packages_skipped_private": 0,
        "packages_failed": 0,
        "total_dependencies": 0,
        "dependencies_with_missing_release": 0,
        "dependencies_with_missing_commit": 0,
        "output_file": None
    }

    try:
        # Step 1: Fetch top packages
        logger.info(f"Fetching top {top_n} packages by weekly downloads...")
        top_packages = npm_client.get_top_packages(top_n)
        logger.info(f"Retrieved {len(top_packages)} top packages")

        all_dependencies: List[Dict[str, Any]] = []

        # Step 2: Process each package
        for idx, pkg_info in enumerate(top_packages):
            package_name = pkg_info.get("name", "unknown")
            logger.info(f"[{idx+1}/{len(top_packages)}] Processing: {package_name}")

            try:
                # Check if package is private
                if pkg_info.get("private", False):
                    logger.warning(f"Skipping private package: {package_name}")
                    stats["packages_skipped_private"] += 1
                    continue

                # Resolve full dependency tree
                logger.debug(f"Resolving dependency tree for {package_name}")
                deps = resolver.resolve_package_dependencies(package_name)

                if not deps:
                    logger.warning(f"No dependencies found for {package_name}")
                    stats["packages_failed"] += 1
                    continue

                # Process each dependency
                for dep in deps:
                    dep_dict = dep.model_dump() if hasattr(dep, 'model_dump') else dict(dep)
                    
                    # Track missing metadata
                    if not dep_dict.get("last_release_date"):
                        stats["dependencies_with_missing_release"] += 1
                    if not dep_dict.get("last_commit_date"):
                        stats["dependencies_with_missing_commit"] += 1

                    all_dependencies.append(dep_dict)

                stats["packages_processed"] += 1
                stats["total_dependencies"] += len(deps)

                # Log progress
                if (idx + 1) % 10 == 0:
                    logger.info(f"Progress: {idx+1}/{len(top_packages)} packages, "
                              f"{len(all_dependencies)} total dependencies collected")

            except Exception as e:
                logger.error(f"Failed to process package {package_name}: {str(e)}", exc_info=True)
                stats["packages_failed"] += 1
                continue

        # Step 3: Save results
        if all_dependencies:
            output_file = output_path / "dependencies_raw.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_dependencies, f, indent=2, default=str)
            
            # Generate checksum
            checksum = generate_checksum(output_file)
            checksum_file = output_path / "dependencies_raw.json.sha256"
            with open(checksum_file, 'w', encoding='utf-8') as f:
                f.write(f"{checksum}  dependencies_raw.json\n")
            
            stats["output_file"] = str(output_file)
            logger.info(f"Saved {len(all_dependencies)} dependencies to {output_file}")
            logger.info(f"Checksum saved to {checksum_file}")
        else:
            logger.warning("No dependencies collected, no output file generated")

        stats["end_time"] = datetime.now().isoformat()
        stats["success"] = True

    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
        stats["end_time"] = datetime.now().isoformat()
        stats["success"] = False
        stats["error"] = str(e)

    # Save statistics
    stats_file = output_path / "collection_stats.json"
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
    logger.info(f"Statistics saved to {stats_file}")

    return stats


def main():
    """Entry point for CLI execution."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Collect NPM dependency data for analysis"
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=100,
        help="Number of top packages to analyze (default: 100)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for collected data (default: data/processed)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only collect metadata without fetching full data"
    )

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("NPM Dependency Data Collection Pipeline")
    logger.info("=" * 60)

    results = collect_data(
        top_n=args.top_n,
        output_dir=args.output_dir,
        dry_run=args.dry_run
    )

    logger.info("=" * 60)
    logger.info("Collection Summary")
    logger.info("=" * 60)
    logger.info(f"Success: {results.get('success', False)}")
    logger.info(f"Packages processed: {results.get('packages_processed', 0)}")
    logger.info(f"Packages skipped (private): {results.get('packages_skipped_private', 0)}")
    logger.info(f"Packages failed: {results.get('packages_failed', 0)}")
    logger.info(f"Total dependencies collected: {results.get('total_dependencies', 0)}")
    logger.info(f"Dependencies with missing release date: {results.get('dependencies_with_missing_release', 0)}")
    logger.info(f"Dependencies with missing commit date: {results.get('dependencies_with_missing_commit', 0)}")
    
    if results.get("output_file"):
        logger.info(f"Output file: {results['output_file']}")
    
    if not results.get("success"):
        logger.error("Pipeline completed with errors")
        sys.exit(1)
    else:
        logger.info("Pipeline completed successfully")
        sys.exit(0)


if __name__ == "__main__":
    main()