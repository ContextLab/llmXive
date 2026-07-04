import os
import sys
import json
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.services.npm_client import NpmClient
from src.services.github_client import GithubClient
from src.services.audit_client import AuditClient
from src.services.dependency_resolver import DependencyResolver
from src.config.settings import get_config

def main():
    """
    Orchestrates data collection for User Story 1.
    Fetches top packages, resolves dependencies, and saves raw data.
    """
    print("Starting data collection pipeline (T016)...")
    config = get_config()
    
    npm_client = NpmClient(config)
    github_client = GithubClient(config)
    audit_client = AuditClient(config)
    resolver = DependencyResolver(npm_client, github_client, audit_client)
    
    # Fetch top packages
    packages = npm_client.get_top_packages(limit=5)
    all_deps = []
    
    for pkg in packages:
        pkg_name = pkg.get('name')
        print(f"Processing {pkg_name}...")
        try:
            deps = resolver.resolve_dependencies(pkg_name)
            # Convert to dict for JSON serialization
            for d in deps:
                d_dict = d.model_dump()
                # Convert dates to strings
                if d_dict.get('last_release_date'):
                    d_dict['last_release_date'] = d_dict['last_release_date'].isoformat()
                if d_dict.get('last_commit_date'):
                    d_dict['last_commit_date'] = d_dict['last_commit_date'].isoformat()
                all_deps.append(d_dict)
        except Exception as e:
            print(f"Error: {e}")
            continue
    
    # Save to cache
    output_dir = project_root / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    cache_path = output_dir / "dependencies_raw.json"
    with open(cache_path, 'w') as f:
        json.dump(all_deps, f, indent=2)
    
    print(f"Saved {len(all_deps)} dependencies to {cache_path}")
    return all_deps

if __name__ == "__main__":
    main()
