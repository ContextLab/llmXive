from typing import List, Dict, Any, Optional
from src.services.npm_client import NpmClient
from src.services.github_client import GithubClient
from src.services.audit_client import AuditClient
from src.models.data_models import Dependency
from datetime import datetime, timezone

class DependencyResolver:
    def __init__(self, npm_client: NpmClient, github_client: GithubClient, audit_client: AuditClient):
        self.npm_client = npm_client
        self.github_client = github_client
        self.audit_client = audit_client

    def resolve_dependencies(self, package_name: str) -> List[Dependency]:
        """
        Resolves dependencies for a given package.
        Fetches metadata, commit dates, release dates, and vulnerabilities.
        """
        deps = []
        pkg_meta = self.npm_client.get_package_metadata(package_name)
        
        if not pkg_meta:
            return []

        # Extract dependencies from package.json if available in metadata
        # The NPM registry response contains 'versions' with 'dependencies'
        versions = pkg_meta.get("versions", {})
        latest_version = pkg_meta.get("dist-tags", {}).get("latest", "")
        
        if latest_version in versions:
            deps_dict = versions[latest_version].get("dependencies", {})
            
            for dep_name, dep_version in deps_dict.items():
                # Fetch repo info if available (simplified)
                repo_url = pkg_meta.get("repository", {}).get("url", "")
                owner, repo = None, None
                if repo_url:
                    meta = self.github_client.fetch_repository_metadata(repo_url)
                    if meta:
                        owner, repo = meta["owner"], meta["repo"]

                last_commit = None
                last_release = None
                vuln_count = 0

                if owner and repo:
                    last_commit = self.github_client.get_commit_date(owner, repo)
                    last_release = self.github_client.get_release_date(owner, repo)

                # Calculate age
                age_in_days = None
                if last_release:
                    now = datetime.now(timezone.utc)
                    age_in_days = (now - last_release).days

                # Fetch audit data (simplified)
                # audit_data = self.audit_client.fetch_audit_data(dep_name)
                # vuln_count = audit_data.get("vulnerability_count", 0)

                dep_obj = Dependency(
                    package_name=package_name,
                    name=dep_name,
                    version=dep_version,
                    last_release_date=last_release,
                    last_commit_date=last_commit,
                    vulnerability_count=vuln_count,
                    age_in_days=age_in_days
                )
                deps.append(dep_obj)

        return deps
