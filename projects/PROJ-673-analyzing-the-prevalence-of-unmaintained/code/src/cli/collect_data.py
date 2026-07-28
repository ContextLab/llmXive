import os
import sys
import json
from pathlib import Path
from datetime import datetime
from src.services.npm_client import NpmClient
from src.services.github_client import GithubClient
from src.services.audit_client import AuditClient
from src.models.data_models import Dependency, Package
from src.utils.backoff import exponential_backoff

def collect_data(num_packages: int = 10):
    """
    Collects data for the top N NPM packages, including dependencies,
    release dates, and vulnerability counts.
    """
    npm_client = NpmClient()
    github_client = GithubClient()
    audit_client = AuditClient()

    packages = npm_client.get_top_packages(num_packages)
    all_dependencies = []

    for package in packages:
        try:
            repo_url = package.repository.url
            if repo_url:
                owner, repo_name = repo_url.split('/')[-2:]
                commit_date = github_client.get_last_commit_date(owner, repo_name)
                release_date = github_client.get_last_release_date(owner, repo_name)
            else:
                commit_date = None
                release_date = None

            vulnerabilities = audit_client.fetch_audit_data(package.name)

            dependencies = package.dependencies
            for dep_name, dep_version in dependencies.items():
                dependency = Dependency(
                    package_name=package.name,
                    dependency_name=dep_name,
                    dependency_version=dep_version,
                    last_commit_date=commit_date,
                    last_release_date=release_date,
                    vulnerability_count=len(vulnerabilities) if vulnerabilities else 0
                )
                all_dependencies.append(dependency)

        except Exception as e:
            print(f"Error processing package {package.name}: {e}")
            continue

    return all_dependencies


def main():
    """
    Main function to collect data and save it to a JSON file.
    """
    num_packages = 10  # You can make this configurable
    dependencies = collect_data(num_packages)

    output_file = Path("data/processed/dependencies_raw.json")
    with open(output_file, "w") as f:
        json.dump([d.dict() for d in dependencies], f, indent=4)

    print(f"Data collected and saved to {output_file}")


if __name__ == "__main__":
    main()