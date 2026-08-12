"""
Verify Metabolomics Workbench studies for pre-challenge profiles and disease resistance metadata.

This script queries the Metabolomics Workbench API to identify studies containing:
1. Pre-challenge (baseline) metabolite profiles
2. Disease-resistance metadata

It outputs the verified Study IDs to research.md.
"""
import os
import sys
import json
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
RESEARCH_MD_PATH = PROJECT_ROOT / "research.md"

# Metabolomics Workbench API endpoints
MW_API_BASE = "https://www.metabolomicsworkbench.org/rest/studies"
MW_DATA_API = "https://www.metabolomicsworkbench.org/data"

def search_studies(query_terms: List[str]) -> List[Dict[str, Any]]:
    """
    Search Metabolomics Workbench for studies matching query terms.
    
    Args:
        query_terms: List of terms to search for (e.g., ['plant', 'disease'])
        
    Returns:
        List of study metadata dictionaries
    """
    search_url = f"{MW_API_BASE}/search"
    params = {
        "query": " ".join(query_terms),
        "format": "json"
    }
    
    try:
        response = requests.get(search_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Handle different response formats
        if isinstance(data, dict):
            if "studies" in data:
                return data["studies"]
            elif "result" in data and isinstance(data["result"], list):
                return data["result"]
        elif isinstance(data, list):
            return data
            
        return []
    except requests.RequestException as e:
        print(f"Error searching studies: {e}")
        return []

def get_study_metadata(study_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve detailed metadata for a specific study.
    
    Args:
        study_id: Metabolomics Workbench Study ID (e.g., "ST001234")
        
    Returns:
        Study metadata dictionary or None if not found
    """
    url = f"{MW_API_BASE}/{study_id}"
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            return response.json()
        return None
    except requests.RequestException:
        return None

def check_pre_challenge_profiles(metadata: Dict[str, Any]) -> bool:
    """
    Check if study contains pre-challenge/baseline metabolite profiles.
    
    Args:
        metadata: Study metadata dictionary
        
    Returns:
        True if pre-challenge profiles are found
    """
    # Check study title and abstract for keywords
    title = metadata.get("study_title", "").lower()
    abstract = metadata.get("study_abstract", "").lower()
    text = f"{title} {abstract}"
    
    pre_challenge_keywords = [
        "pre-challenge", "baseline", "before challenge", "before infection",
        "pre-infection", "control", "uninfected", "healthy", "time 0",
        "pre-treatment", "pre-pathogen"
    ]
    
    if any(keyword in text for keyword in pre_challenge_keywords):
        return True
    
    # Check sample metadata if available
    samples = metadata.get("samples", [])
    if samples:
        for sample in samples:
            sample_type = sample.get("sample_type", "").lower()
            sample_time = sample.get("time_point", "").lower()
            
            if any(k in sample_type for k in ["baseline", "control", "healthy"]):
                return True
            if any(k in sample_time for k in ["0", "pre", "before"]):
                return True
                
    return False

def check_disease_resistance_metadata(metadata: Dict[str, Any]) -> bool:
    """
    Check if study contains disease-resistance metadata.
    
    Args:
        metadata: Study metadata dictionary
        
    Returns:
        True if disease-resistance metadata is found
    """
    title = metadata.get("study_title", "").lower()
    abstract = metadata.get("study_abstract", "").lower()
    text = f"{title} {abstract}"
    
    resistance_keywords = [
        "resistance", "susceptible", "disease", "pathogen", "infection",
        "challenge", "immune", "defense", "tolerance", "severity",
        "lesion", "symptom", "antifungal", "antibacterial", "virus"
    ]
    
    if any(keyword in text for keyword in resistance_keywords):
        return True
    
    # Check for phenotype data
    phenotypes = metadata.get("phenotypes", [])
    if phenotypes:
        for phen in phenotypes:
            phen_name = phen.get("phenotype_name", "").lower()
            phen_desc = phen.get("phenotype_description", "").lower()
            phen_text = f"{phen_name} {phen_desc}"
            
            if any(k in phen_text for k in ["resistance", "susceptible", "disease", "severity"]):
                return True
                
    return False

def verify_studies(query_terms: List[str], min_studies: int = 2) -> List[Dict[str, Any]]:
    """
    Verify studies that contain both pre-challenge profiles and disease-resistance metadata.
    
    Args:
        query_terms: Terms to search for
        min_studies: Minimum number of studies to find
        
    Returns:
        List of verified study dictionaries
    """
    print(f"Searching for studies with terms: {query_terms}")
    all_studies = search_studies(query_terms)
    
    if not all_studies:
        print("No studies found in initial search")
        return []
    
    print(f"Found {len(all_studies)} candidate studies")
    
    verified_studies = []
    
    for study in all_studies:
        study_id = study.get("study_id")
        if not study_id:
            continue
            
        print(f"Checking study: {study_id}")
        
        # Get full metadata
        full_metadata = get_study_metadata(study_id)
        if not full_metadata:
            continue
            
        # Check for required components
        has_pre_challenge = check_pre_challenge_profiles(full_metadata)
        has_resistance = check_disease_resistance_metadata(full_metadata)
        
        if has_pre_challenge and has_resistance:
            verified_studies.append({
                "study_id": study_id,
                "title": full_metadata.get("study_title", "Unknown"),
                "pre_challenge": has_pre_challenge,
                "resistance_metadata": has_resistance,
                "url": f"https://www.metabolomicsworkbench.org/data/study.php?STUDY_ID={study_id}"
            })
            print(f"  ✓ Verified: {study_id}")
            if len(verified_studies) >= min_studies:
                break
        else:
            print(f"  ✗ Skipped: {study_id} (pre_challenge={has_pre_challenge}, resistance={has_resistance})")
    
    return verified_studies

def update_research_md(verified_studies: List[Dict[str, Any]]) -> None:
    """
    Update research.md with verified study IDs.
    
    Args:
        verified_studies: List of verified study dictionaries
    """
    if not RESEARCH_MD_PATH.exists():
        print(f"Warning: {RESEARCH_MD_PATH} does not exist. Creating new file.")
        RESEARCH_MD_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Read existing content
    try:
        with open(RESEARCH_MD_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {RESEARCH_MD_PATH}: {e}")
        content = "# Research Notes\n\n"
    
    # Prepare study section
    study_section = "\n## Verified Metabolomics Workbench Studies\n\n"
    study_section += f"Verified on: {Path(__file__).parent}\n\n"
    study_section += "| Study ID | Title | Pre-Challenge | Resistance Metadata |\n"
    study_section += "|----------|-------|---------------|---------------------|\n"
    
    for study in verified_studies:
        study_section += f"| {study['study_id']} | {study['title']} | ✅ | ✅ |\n"
    
    study_section += "\n### Study Details\n\n"
    
    for study in verified_studies:
        study_section += f"**{study['study_id']}**: {study['title']}\n"
        study_section += f"- URL: {study['url']}\n\n"
    
    # Check if we already have a verified studies section
    if "## Verified Metabolomics Workbench Studies" in content:
        # Replace existing section
        parts = content.split("## Verified Metabolomics Workbench Studies")
        content = parts[0] + study_section
    else:
        # Append to end
        content += study_section
    
    # Write back
    try:
        with open(RESEARCH_MD_PATH, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Successfully updated {RESEARCH_MD_PATH}")
    except Exception as e:
        print(f"Error writing {RESEARCH_MD_PATH}: {e}")

def main():
    """Main entry point for study verification."""
    print("=" * 60)
    print("Metabolomics Workbench Study Verification")
    print("=" * 60)
    
    # Search terms for plant disease metabolomics
    query_terms = [
        "plant", "disease", "metabolomics", "resistance",
        "pathogen", "infection", "challenge"
    ]
    
    # Verify studies
    verified = verify_studies(query_terms, min_studies=2)
    
    if len(verified) < 2:
        print(f"\n⚠️  WARNING: Only found {len(verified)} verified studies. Minimum 2 required.")
        print("Attempting broader search...")
        
        # Broader search
        broader_terms = ["plant", "metabolomics"]
        broader_results = verify_studies(broader_terms, min_studies=2)
        
        # Merge results (avoid duplicates)
        existing_ids = {s["study_id"] for s in verified}
        for study in broader_results:
            if study["study_id"] not in existing_ids:
                verified.append(study)
                if len(verified) >= 2:
                    break
    
    if len(verified) >= 2:
        print(f"\n✅ Successfully verified {len(verified)} studies:")
        for study in verified:
            print(f"   - {study['study_id']}: {study['title'][:50]}...")
        
        update_research_md(verified)
        print(f"\n📝 Study IDs documented in {RESEARCH_MD_PATH}")
        return 0
    else:
        print(f"\n❌ FAILED: Could not find {2} verified studies with required metadata.")
        print("The pipeline cannot proceed without valid study IDs.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
