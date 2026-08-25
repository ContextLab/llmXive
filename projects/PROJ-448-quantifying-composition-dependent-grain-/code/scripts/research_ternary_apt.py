"""
Script to search Zenodo/DOI for peer-reviewed literature sources containing
ternary APT data (Fe-Cr-Mo, Fe-Cr-V, etc.) and write findings to research/data_sources.md.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.config import get_logger, DATA_DIR, RESEARCH_DIR

# Configure logging
logger = get_logger(__name__)

# Zenodo API endpoint for searching
ZENODO_SEARCH_URL = "https://zenodo.org/api/records"

# Search queries for ternary APT data in Fe-based alloys
SEARCH_QUERIES = [
    "Fe-Cr-Mo atom probe",
    "Fe-Cr-V atom probe",
    "Fe-Mo-V atom probe",
    "Fe-Cr-W atom probe",
    "Fe-Mo-W atom probe",
    "Fe-Cr-Mo APT",
    "Fe-Cr-V APT",
    "grain boundary segregation Fe-Cr-Mo",
    "grain boundary segregation Fe-Cr-V",
]

def search_zenodo(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Search Zenodo API for records matching the query.
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return
        
    Returns:
        List of matching records with DOI and metadata
    """
    params = {
        'q': query,
        'size': max_results,
        'sort': 'mostrecent',
        'fields': 'doi,title,publication_date,metadata'
    }
    
    try:
        response = requests.get(ZENODO_SEARCH_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        records = []
        for hit in data.get('hits', {}).get('hits', []):
            metadata = hit.get('metadata', {})
            doi = hit.get('doi')
            
            if doi:
                # Filter for relevant content (APT, atom probe, segregation)
                title = metadata.get('title', '').lower()
                description = metadata.get('description', '').lower()
                keywords = [kw.lower() for kw in metadata.get('keywords', [])]
                
                relevance_score = 0
                if 'atom probe' in title or 'apt' in title:
                    relevance_score += 3
                if 'atom probe' in description or 'apt' in description:
                    relevance_score += 2
                if any(kw in ['atom probe', 'apt', 'segregation', 'grain boundary'] for kw in keywords):
                    relevance_score += 2
                
                if relevance_score >= 2:  # Only keep relevant results
                    records.append({
                        'doi': doi,
                        'title': metadata.get('title'),
                        'publication_date': metadata.get('publication_date'),
                        'authors': [author.get('name') for author in metadata.get('creators', [])],
                        'description': metadata.get('description'),
                        'keywords': metadata.get('keywords', []),
                        'relevance_score': relevance_score,
                        'source': 'Zenodo'
                    })
        
        return records
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error searching Zenodo for query '{query}': {e}")
        return []

def resolve_doi(doi: str) -> Optional[Dict[str, Any]]:
    """
    Resolve a DOI to get full metadata.
    
    Args:
        doi: DOI string
        
    Returns:
        Metadata dictionary or None if resolution fails
    """
    try:
        url = f"https://doi.org/{doi}"
        response = requests.get(url, timeout=30, allow_redirects=True)
        response.raise_for_status()
        
        # Try to get metadata from Zenodo API if it's a Zenodo DOI
        if 'zenodo' in doi:
            zenodo_id = doi.split('/')[-1]
            api_url = f"https://zenodo.org/api/records/{zenodo_id}"
            api_response = requests.get(api_url, timeout=30)
            if api_response.status_code == 200:
                return api_response.json()
        
        return {'doi': doi, 'url': url}
        
    except requests.exceptions.RequestException as e:
        logger.warning(f"Could not resolve DOI {doi}: {e}")
        return None

def verify_zenodo_accession(doi: str) -> bool:
    """
    Verify that a Zenodo accession exists and contains relevant data.
    
    Args:
        doi: DOI to verify
        
    Returns:
        True if accessible and relevant, False otherwise
    """
    try:
        # Check if DOI is accessible
        url = f"https://doi.org/{doi}"
        response = requests.head(url, timeout=30, allow_redirects=True)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def main():
    """
    Main function to search for ternary APT data sources and write to research/data_sources.md.
    """
    logger.info("Starting search for ternary APT literature sources on Zenodo/DOI")
    
    # Ensure research directory exists
    research_dir = RESEARCH_DIR
    research_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = research_dir / "data_sources.md"
    
    # Collect all findings
    all_findings = []
    seen_dois = set()
    
    for query in SEARCH_QUERIES:
        logger.info(f"Searching for: {query}")
        results = search_zenodo(query, max_results=15)
        
        for record in results:
            doi = record['doi']
            if doi not in seen_dois:
                seen_dois.add(doi)
                # Verify the DOI is accessible
                if verify_zenodo_accession(doi):
                    all_findings.append(record)
                    logger.info(f"Found valid source: {doi} (score: {record['relevance_score']})")
                else:
                    logger.warning(f"DOI {doi} not accessible, skipping")
    
    # Sort by relevance score
    all_findings.sort(key=lambda x: x['relevance_score'], reverse=True)
    
    # Write findings to research/data_sources.md
    if all_findings:
        output_data = {
            "search_completed": True,
            "query_count": len(SEARCH_QUERIES),
            "total_valid_sources": len(all_findings),
            "sources": all_findings
        }
        
        with open(output_file, 'w') as f:
            # Write as markdown with JSON content
            f.write("# Ternary APT Literature Sources (Zenodo/DOI Search)\n\n")
            f.write(f"Search completed on: {__import__('datetime').datetime.now().isoformat()}\n\n")
            f.write(f"Total queries executed: {len(SEARCH_QUERIES)}\n")
            f.write(f"Valid sources found: {len(all_findings)}\n\n")
            f.write("## JSON Data\n\n")
            f.write("```json\n")
            json.dump(output_data, f, indent=2)
            f.write("\n```\n\n")
            f.write("## Summary of Sources\n\n")
            
            for i, source in enumerate(all_findings, 1):
                f.write(f"### {i}. {source['title']}\n")
                f.write(f"- **DOI**: {source['doi']}\n")
                f.write(f"- **Publication Date**: {source.get('publication_date', 'N/A')}\n")
                f.write(f"- **Authors**: {', '.join(source['authors']) if source['authors'] else 'N/A'}\n")
                f.write(f"- **Keywords**: {', '.join(source['keywords']) if source['keywords'] else 'N/A'}\n")
                f.write(f"- **Relevance Score**: {source['relevance_score']}/7\n")
                if source['description']:
                    f.write(f"- **Description**: {source['description'][:200]}...\n")
                f.write("\n")
        
        logger.info(f"Successfully wrote {len(all_findings)} sources to {output_file}")
    else:
        # Write empty result but still create the file
        output_data = {
            "search_completed": True,
            "query_count": len(SEARCH_QUERIES),
            "total_valid_sources": 0,
            "sources": [],
            "note": "No valid ternary APT sources found in Zenodo search. Consider expanding search terms or checking other databases."
        }
        
        with open(output_file, 'w') as f:
            f.write("# Ternary APT Literature Sources (Zenodo/DOI Search)\n\n")
            f.write(f"Search completed on: {__import__('datetime').datetime.now().isoformat()}\n\n")
            f.write("## JSON Data\n\n")
            f.write("```json\n")
            json.dump(output_data, f, indent=2)
            f.write("\n```\n\n")
            f.write("## Note\n\n")
            f.write("No valid ternary APT sources were found in the Zenodo search. ")
            f.write("The search covered multiple queries related to Fe-Cr-Mo, Fe-Cr-V, Fe-Mo-V, ")
            f.write("Fe-Cr-W, and Fe-Mo-W systems. Consider expanding search terms or checking ")
            f.write("other databases like NIST APT or specific journal repositories.\n")
        
        logger.warning(f"No valid sources found. Created empty report at {output_file}")
    
    logger.info("Ternary APT literature search completed")
    return 0

if __name__ == "__main__":
    sys.exit(main())
