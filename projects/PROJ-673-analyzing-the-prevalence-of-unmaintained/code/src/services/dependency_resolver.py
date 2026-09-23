"""
Dependency Resolver Service for NPM Packages.

This module implements the recursive dependency tree resolver to flatten
direct and transitive dependencies for NPM packages (FR-002).
"""
from typing import List, Dict, Any, Optional, Set
from src.services.npm_client import NpmClient
from src.services.github_client import GithubClient
from src.services.audit_client import AuditClient
from src.models.data_models import Dependency
from src.utils.cache import save_response_to_cache, load_from_cache
from src.utils.logging_config import log_api_call
from datetime import datetime, timezone
import logging
import time

logger = logging.getLogger(__name__)

class DependencyResolver:
    """
    Recursively resolves dependency trees for NPM packages, flattening
    direct and transitive dependencies into a single list of Dependency objects.
    """

    def __init__(self, npm_client: NpmClient, github_client: GithubClient, audit_client: AuditClient):
        self.npm_client = npm_client
        self.github_client = github_client
        self.audit_client = audit_client
        self._visited_packages: Set[str] = set()

    def _resolve_package_dependencies(self, package_name: str, version: str, depth: int = 0, max_depth: int = 5) -> List[Dict[str, Any]]:
        """
        Recursively fetches and resolves dependencies for a specific package version.

        Args:
            package_name: The name of the NPM package.
            version: The version of the package.
            depth: Current recursion depth.
            max_depth: Maximum recursion depth to prevent infinite loops.

        Returns:
            A list of dependency dictionaries containing metadata.
        """
        if depth >= max_depth:
            logger.warning(f"Max depth {max_depth} reached for {package_name}@{version}. Stopping recursion.")
            return []

        cache_key = {
            "service": "npm",
            "endpoint": "package_info",
            "package": package_name,
            "version": version
        }
        
        cached = load_from_cache(cache_key)
        if cached:
            logger.info(f"Cache hit for {package_name}@{version}")
            package_data = cached
        else:
            logger.info(f"Fetching metadata for {package_name}@{version}")
            try:
                package_data = self.npm_client.get_package_metadata(package_name, version)
                if package_data:
                    save_response_to_cache(cache_key, package_data)
            except Exception as e:
                logger.error(f"Failed to fetch metadata for {package_name}@{version}: {e}")
                return []

        if not package_data or "dependencies" not in package_data:
            return []

        dependencies = []
        direct_deps = package_data.get("dependencies", {})

        for dep_name, dep_version_spec in direct_deps.items():
            # Normalize version spec (e.g., "^1.0.0" -> "1.0.0" if possible, or keep as is)
            # For simplicity in this resolver, we attempt to resolve the exact version if possible,
            # otherwise we treat the spec as the version key for the next fetch.
            # In a real production system, we would resolve semver ranges to exact versions.
            # Here we assume the spec provided is sufficient to fetch or we fetch the latest.
            
            # Avoid infinite loops by checking visited set
            package_id = f"{dep_name}@{dep_version_spec}"
            if package_id in self._visited_packages:
                logger.debug(f"Skipping already visited package: {package_id}")
                continue
            
            self._visited_packages.add(package_id)

            # Fetch dependency metadata
            dep_metadata = self.npm_client.get_package_metadata(dep_name, dep_version_spec)
            if not dep_metadata:
                logger.warning(f"Could not resolve metadata for dependency: {dep_name}@{dep_version_spec}")
                continue

            dep_version = dep_metadata.get("version", dep_version_spec)
            repo_url = dep_metadata.get("repository", {}).get("url")
            repo_name = None
            
            if repo_url and "github.com" in repo_url:
                # Extract repo name from URL (e.g., https://github.com/user/repo -> user/repo)
                parts = repo_url.split("/")
                if len(parts) >= 2:
                    repo_name = f"{parts[-2]}/{parts[-1].replace('.git', '')}"

            # Fetch GitHub dates if repo is available
            last_commit = None
            last_release = None
            if repo_name:
                try:
                    last_commit = self.github_client.get_last_commit_date(repo_name)
                    last_release = self.github_client.get_last_release_date(repo_name)
                except Exception as e:
                    logger.warning(f"Failed to fetch GitHub dates for {repo_name}: {e}")

            # Fetch audit data
            vulnerability_count = 0
            try:
                audit_data = self.audit_client.fetch_audit_data(dep_name)
                if audit_data:
                    vulnerabilities = audit_data.get("vulnerabilities", {})
                    # Sum up all severity counts or just count entries
                    vulnerability_count = len(vulnerabilities) if isinstance(vulnerabilities, dict) else 0
            except Exception as e:
                logger.warning(f"Failed to fetch audit data for {dep_name}: {e}")

            # Create Dependency object
            dep_obj = {
                "name": dep_name,
                "version": dep_version,
                "last_commit_date": last_commit.isoformat() if last_commit else None,
                "last_release_date": last_release.isoformat() if last_release else None,
                "vulnerability_count": vulnerability_count,
                "depth": depth + 1,
                "parent": f"{package_name}@{version}"
            }
            dependencies.append(dep_obj)

            # Recursively resolve transitive dependencies
            transitive_deps = self._resolve_package_dependencies(dep_name, dep_version, depth + 1, max_depth)
            dependencies.extend(transitive_deps)

        return dependencies

    def resolve_full_tree(self, package_name: str, version: str = "latest", max_depth: int = 5) -> List[Dict[str, Any]]:
        """
        Resolves the full dependency tree for a given package.

        Args:
            package_name: The name of the root package.
            version: The version of the root package.
            max_depth: Maximum depth of transitive dependencies to resolve.

        Returns:
            A flat list of all dependencies (direct and transitive) with metadata.
        """
        self._visited_packages.clear()
        logger.info(f"Starting dependency resolution for {package_name}@{version}")
        
        # Resolve root package first
        root_deps = self._resolve_package_dependencies(package_name, version, depth=0, max_depth=max_depth)
        
        logger.info(f"Resolved {len(root_deps)} dependencies for {package_name}")
        return root_deps

    def flatten_to_dependencies(self, raw_deps: List[Dict[str, Any]]) -> List[Dependency]:
        """
        Converts raw dependency dictionaries into typed Dependency model objects.

        Args:
            raw_deps: List of raw dependency dictionaries.

        Returns:
            List of Dependency objects.
        """
        dependencies = []
        for dep in raw_deps:
            try:
                dep_obj = Dependency(
                    name=dep.get("name"),
                    version=dep.get("version"),
                    last_commit_date=datetime.fromisoformat(dep["last_commit_date"]) if dep.get("last_commit_date") else None,
                    last_release_date=datetime.fromisoformat(dep["last_release_date"]) if dep.get("last_release_date") else None,
                    vulnerability_count=dep.get("vulnerability_count", 0),
                    depth=dep.get("depth", 0),
                    parent=dep.get("parent")
                )
                dependencies.append(dep_obj)
            except Exception as e:
                logger.error(f"Failed to parse dependency {dep.get('name')}: {e}")
                continue
        
        return dependencies

def main():
    """
    Entry point for testing the DependencyResolver.
    """
    logging.basicConfig(level=logging.INFO)
    
    # Initialize clients
    npm_client = NpmClient()
    github_client = GithubClient()
    audit_client = AuditClient()
    
    resolver = DependencyResolver(npm_client, github_client, audit_client)
    
    # Example: Resolve a popular package
    # Using 'express' as a test case
    package_name = "express"
    version = "latest"
    
    print(f"Resolving dependencies for {package_name}...")
    raw_deps = resolver.resolve_full_tree(package_name, version, max_depth=3)
    
    print(f"Found {len(raw_deps)} dependencies.")
    
    # Convert to typed objects
    typed_deps = resolver.flatten_to_dependencies(raw_deps)
    
    # Print summary
    for dep in typed_deps[:10]:
        print(f"- {dep.name}@{dep.version} (Depth: {dep.depth}, Vulns: {dep.vulnerability_count})")
        
    if len(typed_deps) > 10:
        print(f"... and {len(typed_deps) - 10} more.")

if __name__ == "__main__":
    main()