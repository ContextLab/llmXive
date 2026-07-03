"""
Data acquisition utilities for repository filtering.

This module contains the interface for filtering repositories based on
project constraints (license, CI, issues) as defined in the PESTO filter logic.
"""
from typing import List, Dict, Any, Set
import logging

# Define valid license types as per project requirements
VALID_LICENSES: Set[str] = {
    "MIT", "Apache-2.0", "BSD-3-Clause", "BSD-2-Clause", 
    "GPL-3.0", "GPL-2.0", "LGPL-3.0", "ISC", "MPL-2.0"
}

logger = logging.getLogger(__name__)

def filter_repos(repos: List[Dict[str, Any]], valid_licenses: Set[str] = None) -> List[Dict[str, Any]]:
    """
    Filter a list of repositories based on license validity and other PESTO criteria.
    
    Args:
        repos: List of repository metadata dictionaries.
        valid_licenses: Optional set of allowed license identifiers. Defaults to VALID_LICENSES.
        
    Returns:
        A list of repositories that pass the license filter.
        
    Raises:
        ValueError: If a repository has an invalid or missing license type.
    """
    if valid_licenses is None:
        valid_licenses = VALID_LICENSES
        
    filtered = []
    
    for repo in repos:
        license_info = repo.get("license")
        if not license_info:
            logger.warning(f"Repository {repo.get('full_name', 'unknown')} has no license info. Skipping.")
            # Per PESTO filter, missing license usually means exclusion, 
            # but the specific contract for this task requires raising ValueError for invalid types.
            # We treat 'None' as an invalid license type for the purpose of this contract test.
            raise ValueError(f"Repository {repo.get('full_name', 'unknown')} has an invalid license type: None")
            
        license_spdx = license_info.get("spdx_id")
        
        if license_spdx not in valid_licenses:
            raise ValueError(f"Repository {repo.get('full_name', 'unknown')} has an invalid license type: {license_spdx}")
            
        filtered.append(repo)
        
    return filtered
