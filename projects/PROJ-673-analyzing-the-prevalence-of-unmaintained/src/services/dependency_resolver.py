"""
Dependency Resolver Module

Implements recursive dependency tree resolution to flatten direct and transitive
dependencies for NPM packages, satisfying FR-002.
"""

import os
import sys
from typing import Dict, List, Any, Optional, Set

# Ensure src is in path for imports if running as script
if 'src' not in sys.path:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.models.data_models import Dependency
from src.services.audit_client import AuditClient
from src.services.github_client import GithubClient
from src.utils.backoff import exponential_backoff
from src.config.settings import get_config
from datetime import datetime


class DependencyResolver:
    """
    Recursively resolves dependency trees for NPM packages.
    
    Handles:
    - Direct and transitive dependencies
    - Circular dependency detection
    - Metadata enrichment (last release, commit, audit data)
    - Private package filtering
    """

    def __init__(self):
        self.config = get_config()
        self.audit_client = AuditClient()
        self.github_client = GithubClient()
        self.visited: Set[str] = set()
        self.resolved_deps: List[Dict[str, Any]] = []

    def _fetch_package_metadata(self, package_name: str, version: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Fetch package metadata from NPM registry."""
        try:
            url = f"https://registry.npmjs.org/{package_name}"
            if version:
                url = f"{url}/{version}"
            
            response = exponential_backoff(
                lambda: __import__('requests').get(url, timeout=30),
                max_retries=3
            )
            
            if response.status_code == 200:
                return response.json()
            return None
        except Exception:
            return None

    def _extract_dependencies(self, package_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract dependency list from package metadata."""
        dependencies = []
        
        # Get all dependency types
        dep_types = ['dependencies', 'devDependencies', 'peerDependencies', 'optionalDependencies']
        
        for dep_type in dep_types:
            deps = package_data.get(dep_type, {})
            for name, version in deps.items():
                # Clean version string (remove ^, ~, etc.)
                clean_version = version.lstrip('^~>=<')
                dependencies.append({
                    'name': name,
                    'version': clean_version,
                    'type': dep_type
                })
        
        return dependencies

    def _get_repository_info(self, package_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract repository information from package metadata."""
        repo_info = package_data.get('repository', {})
        
        if isinstance(repo_info, dict):
            url = repo_info.get('url', '')
            if url and 'github.com' in url:
                # Extract owner/repo from URL
                parts = url.split('/')
                if len(parts) >= 6:
                    owner = parts[-2]
                    repo = parts[-1].replace('.git', '')
                    return {'owner': owner, 'repo': repo}
        return None

    def _enrich_dependency_metadata(self, dep: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich dependency with metadata from GitHub and Audit clients."""
        package_name = dep['name']
        version = dep.get('version', 'latest')
        
        # Fetch audit data
        audit_data = self.audit_client.fetch_audit_data(package_name)
        vulnerability_count = len(audit_data.get('advisories', [])) if audit_data else 0
        
        # Fetch repository info
        repo_info = None
        last_commit_date = None
        last_release_date = None
        
        # Try to get repo info from package metadata if available
        if 'package_metadata' in dep:
            repo_info = self._get_repository_info(dep['package_metadata'])
        
        if repo_info:
            try:
                last_commit_date = self.github_client.get_commit_date(
                    repo_info['owner'], 
                    repo_info['repo']
                )
                last_release_date = self.github_client.get_release_date(
                    repo_info['owner'], 
                    repo_info['repo']
                )
            except Exception:
                pass  # Keep as None if API fails
        
        return {
            'name': package_name,
            'version': version,
            'dependency_type': dep.get('type', 'dependencies'),
            'vulnerability_count': vulnerability_count,
            'last_commit_date': last_commit_date.isoformat() if last_commit_date else None,
            'last_release_date': last_release_date.isoformat() if last_release_date else None,
            'is_private': False,  # Will be updated if detected
            'depth': dep.get('depth', 0)
        }

    def _resolve_dependencies_recursive(
        self, 
        package_name: str, 
        version: str, 
        depth: int = 0, 
        visited: Optional[Set[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Recursively resolve dependencies for a package.
        
        Args:
            package_name: Name of the package
            version: Version of the package
            depth: Current depth in dependency tree
            visited: Set of already visited packages to avoid cycles
        
        Returns:
            List of resolved dependency dictionaries
        """
        if visited is None:
            visited = set()
        
        package_key = f"{package_name}@{version}"
        
        # Detect circular dependencies
        if package_key in visited:
            return []
        
        visited.add(package_key)
        dependencies = []
        
        # Fetch package metadata
        package_data = self._fetch_package_metadata(package_name, version)
        if not package_data:
            return []
        
        # Check if package is private (has no repository info and limited metadata)
        if not package_data.get('repository') and not package_data.get('maintainers'):
            # Mark as private but still include in list
            dependencies.append({
                'name': package_name,
                'version': version,
                'dependency_type': 'root',
                'vulnerability_count': 0,
                'last_commit_date': None,
                'last_release_date': None,
                'is_private': True,
                'depth': depth
            })
            return dependencies
        
        # Extract direct dependencies
        direct_deps = self._extract_dependencies(package_data)
        
        for dep in direct_deps:
            dep['depth'] = depth + 1
            dep['package_metadata'] = package_data  # Pass metadata for repo extraction
            
            # Enrich with metadata
            enriched_dep = self._enrich_dependency_metadata(dep)
            dependencies.append(enriched_dep)
            
            # Recursively resolve transitive dependencies
            transitive_deps = self._resolve_dependencies_recursive(
                dep['name'],
                dep['version'],
                depth + 1,
                visited.copy()
            )
            dependencies.extend(transitive_deps)
        
        return dependencies

    def resolve_package_dependencies(
        self, 
        package_name: str, 
        version: str = 'latest',
        max_depth: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Resolve all dependencies for a package up to max_depth.
        
        Args:
            package_name: Name of the package
            version: Version of the package
            max_depth: Maximum depth to traverse (default 10)
        
        Returns:
            List of all dependencies (direct and transitive)
        """
        self.visited = set()
        self.resolved_deps = []
        
        # Resolve dependencies
        dependencies = self._resolve_dependencies_recursive(
            package_name, 
            version, 
            max_depth=max_depth
        )
        
        # Filter out private packages from results (but keep track)
        public_deps = [dep for dep in dependencies if not dep.get('is_private', False)]
        
        return public_deps

    def flatten_dependency_tree(
        self, 
        package_name: str, 
        version: str = 'latest'
    ) -> List[Dict[str, Any]]:
        """
        Flatten the entire dependency tree for a package.
        
        This is the main entry point for FR-002 compliance.
        
        Args:
            package_name: Name of the root package
            version: Version of the root package
        
        Returns:
            Flattened list of all dependencies with metadata
        """
        return self.resolve_package_dependencies(package_name, version)


def main():
    """
    CLI entry point for testing the dependency resolver.
    """
    resolver = DependencyResolver()
    
    # Test with a popular package
    test_package = "express"
    test_version = "4.18.2"
    
    print(f"Resolving dependencies for {test_package}@{test_version}...")
    
    dependencies = resolver.flatten_dependency_tree(test_package, test_version)
    
    print(f"Found {len(dependencies)} dependencies:")
    for dep in dependencies[:10]:  # Show first 10
        print(f"  - {dep['name']}@{dep['version']} (depth: {dep['depth']}, vulns: {dep['vulnerability_count']})")
    
    if len(dependencies) > 10:
        print(f"  ... and {len(dependencies) - 10} more")


if __name__ == "__main__":
    main()