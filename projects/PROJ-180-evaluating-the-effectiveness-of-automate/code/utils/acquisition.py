from typing import List, Dict, Any, Set
import logging
import json
import os
from pathlib import Path

# Define the set of allowed open-source licenses based on PESTO criteria
ALLOWED_LICENSES: Set[str] = {
    "MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", 
    "ISC", "MPL-2.0", "LGPL-2.1", "LGPL-3.0", "GPL-3.0", "CC0-1.0"
}

logger = logging.getLogger(__name__)

def filter_repos(repos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter repositories based on PESTO criteria, specifically license validity.
    
    Args:
        repos: List of repository dictionaries containing metadata including 'license'.
        
    Returns:
        List of repositories that pass the license filter.
        
    Raises:
        ValueError: If a repository has an invalid or missing license type.
    """
    filtered_repos = []
    
    for repo in repos:
        license_info = repo.get("license")
        
        if license_info is None:
            error_msg = f"Repository {repo.get('full_name', 'unknown')} has no license information (invalid license type)."
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        spdx_id = license_info.get("spdx_id")
        
        if spdx_id not in ALLOWED_LICENSES:
            error_msg = f"Repository {repo.get('full_name', 'unknown')} has an invalid license type: {spdx_id}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        filtered_repos.append(repo)
        
    return filtered_repos

def run_tool_pipeline(repos: List[Dict[str, Any]], tools: List[str]) -> Dict[str, Any]:
    """
    Placeholder for the tool execution pipeline.
    In a real implementation, this would execute SonarQube, DeepSource, etc.
    """
    logger.info(f"Running tool pipeline for {len(repos)} repos with tools: {tools}")
    return {"status": "placeholder", "repos_processed": len(repos)}