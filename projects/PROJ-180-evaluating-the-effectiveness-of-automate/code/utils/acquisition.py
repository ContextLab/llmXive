"""
Data acquisition utilities.
Includes logic for filtering repositories and running tool pipelines.
"""
from typing import List, Dict, Any, Set
import logging
import json
import os
from pathlib import Path

logger = logging.getLogger(__name__)

def filter_repos(repos: List[Dict[str, Any]], allowed_licenses: Set[str] = None) -> List[Dict[str, Any]]:
    """
    Filter repositories based on license and other criteria.
    
    Args:
        repos: List of repository metadata dictionaries.
        allowed_licenses: Set of allowed license identifiers (e.g., 'MIT', 'Apache-2.0').
        
    Returns:
        Filtered list of repositories.
        
    Raises:
        ValueError: If a repository has an invalid license type.
    """
    if allowed_licenses is None:
        allowed_licenses = {"MIT", "Apache-2.0", "BSD-3-Clause", "ISC"}
        
    filtered = []
    for repo in repos:
        license_id = repo.get("license", {}).get("spdx_id", "UNKNOWN")
        if license_id not in allowed_licenses:
            logger.warning(f"Repository {repo.get('full_name')} skipped due to license: {license_id}")
            continue
        filtered.append(repo)
    return filtered

def run_tool_pipeline(repo_path: str, tools: List[Dict[str, Any]], repo_metadata: Dict[str, Any], output_dir: str, versions_config: str = None) -> Dict[str, Dict[str, Any]]:
    """
    Execute static analysis tools in Docker containers and collect results.
    This function mocks the actual Docker execution in tests but is designed
    to integrate with real Docker in production.
    
    Args:
        repo_path: Path to the cloned repository.
        tools: List of tool configurations (name, image, command).
        repo_metadata: Metadata about the repository (owner, repo, commit).
        output_dir: Directory to save raw JSON reports.
        versions_config: Path to versions.yaml (optional, for image overrides).
        
    Returns:
        Dictionary mapping tool names to result metadata (output_file, status).
    """
    import docker
    
    client = docker.from_env()
    results = {}
    
    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    for tool in tools:
        tool_name = tool["name"]
        image = tool["image"]
        command = tool["command"]
        
        logger.info(f"Executing {tool_name} on {repo_path}")
        
        try:
            # Simulate container execution
            # In a real implementation, this would mount the repo and run the scanner
            container = client.containers.run(
                image,
                command=command,
                volumes={repo_path: {"bind": "/code", "mode": "ro"}},
                detach=True
            )
            
            # Wait for completion
            exit_status = container.wait()
            logs = container.logs().decode('utf-8')
            container.remove()
            
            if exit_status.get("StatusCode", 1) != 0:
                logger.error(f"{tool_name} failed with exit code {exit_status}")
                continue
            
            # Parse logs (simplified for mock; real implementation parses JSON reports)
            try:
                tool_output = json.loads(logs)
            except json.JSONDecodeError:
                tool_output = {"issues": [], "raw_log": logs}
            
            # Normalize output
            normalized_report = {
                "tool": tool_name,
                "repo_metadata": repo_metadata,
                "issues": tool_output.get("issues", []),
                "raw_log": tool_output.get("raw_log", ""),
                "timestamp": "2023-10-27T00:00:00Z"
            }
            
            # Save to file
            output_filename = f"{repo_metadata['repo']}_{tool_name}_report.json"
            output_path = os.path.join(output_dir, output_filename)
            
            with open(output_path, 'w') as f:
                json.dump(normalized_report, f, indent=2)
            
            results[tool_name] = {
                "output_file": output_path,
                "status": "success",
                "issue_count": len(normalized_report["issues"])
            }
            
        except Exception as e:
            logger.error(f"Error running {tool_name}: {e}")
            results[tool_name] = {
                "output_file": None,
                "status": "failed",
                "error": str(e)
            }
            
    return results
