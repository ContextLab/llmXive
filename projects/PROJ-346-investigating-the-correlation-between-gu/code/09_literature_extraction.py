"""
T040a: Literature Extraction Module
Fetches and parses real literature data from PubMed/PMC regarding gut microbiome and cognitive flexibility.
"""
import os
import sys
import json
import logging
import time
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import requests
from bs4 import BeautifulSoup

# Add project root to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))
    from utils import get_project_root_path, get_data_raw_path, setup_logger
else:
    from code.utils import get_project_root_path, get_data_raw_path, setup_logger

# Configuration
PUBLISHED_QUERIES = [
    ("gut microbiome", "cognitive flexibility"),
    ("microbiome", "BDNF"),
    ("SCFA", "HDAC")
]
CONFIDENCE_THRESHOLD = 0.85
MAX_RETRIES = 3
TIMEOUT = 30

logger = setup_logger("literature_extraction")

def get_project_root() -> Path:
    return get_project_root_path()

def get_data_raw() -> Path:
    return get_data_raw_path()

def search_pubmed_ids(queries: List[Tuple[str, str]]) -> List[str]:
    """
    Search PubMed for PMIDs matching the query logic.
    Uses the PubMed ESearch API to retrieve a list of PMIDs.
    """
    pmids = set()
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    
    for term1, term2 in queries:
        query = f'"{term1}" AND "{term2}"'
        params = {
            "db": "pubmed",
            "term": query,
            "retmax": 50,  # Limit to top 50 per query to manage load
            "retmode": "json",
            "usehistory": "y"
        }
        
        attempt = 0
        while attempt < MAX_RETRIES:
            try:
                logger.info(f"Searching PubMed for: {query}")
                response = requests.get(base_url, params=params, timeout=TIMEOUT)
                response.raise_for_status()
                data = response.json()
                
                if "esearchresult" in data and "idlist" in data["esearchresult"]:
                    ids = data["esearchresult"]["idlist"]
                    pmids.update(ids)
                    logger.info(f"Found {len(ids)} IDs for query '{query}'")
                else:
                    logger.warning(f"No results for query '{query}'")
                break
            except requests.exceptions.RequestException as e:
                attempt += 1
                logger.warning(f"Request failed (attempt {attempt}/{MAX_RETRIES}): {e}")
                if attempt < MAX_RETRIES:
                    time.sleep(2 ** attempt)
                else:
                    logger.error(f"Failed to search PubMed after {MAX_RETRIES} attempts.")
                    raise
    
    return list(pmids)

def fetch_abstracts(pmids: List[str]) -> List[Dict[str, Any]]:
    """
    Fetch abstracts for a list of PMIDs using PubMed EFetch.
    """
    abstracts = []
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    
    # PubMed EFetch accepts multiple IDs in one request, but we'll batch them
    # to avoid URL length limits or timeouts.
    batch_size = 20
    
    for i in range(0, len(pmids), batch_size):
        batch = pmids[i:i+batch_size]
        params = {
            "db": "pubmed",
            "id": ",".join(batch),
            "retmode": "xml",
            "rettype": "abstract"
        }
        
        attempt = 0
        while attempt < MAX_RETRIES:
            try:
                logger.info(f"Fetching abstracts for batch {i//batch_size + 1}")
                response = requests.get(base_url, params=params, timeout=TIMEOUT)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, "xml")
                articles = soup.find_all("PubmedArticle")
                
                for article in articles:
                    pmid_elem = article.find("PMID")
                    abstract_elem = article.find("AbstractText")
                    
                    if pmid_elem and abstract_elem:
                        abstracts.append({
                            "pmid": pmid_elem.get_text(),
                            "abstract_text": abstract_elem.get_text() if abstract_elem.text else ""
                        })
                
                break
            except requests.exceptions.RequestException as e:
                attempt += 1
                logger.warning(f"Fetch failed (attempt {attempt}/{MAX_RETRIES}): {e}")
                if attempt < MAX_RETRIES:
                    time.sleep(2 ** attempt)
                else:
                    logger.error(f"Failed to fetch abstracts after {MAX_RETRIES} attempts.")
                    raise
    
    return abstracts

def extract_effect_sizes(text: str) -> List[Tuple[float, float]]:
    """
    Extract effect sizes (r, beta) from abstract text using regex.
    Returns a list of tuples: (value, confidence_score).
    Confidence is heuristic based on context proximity.
    """
    # Patterns for correlation (r) and beta coefficients
    # Matches: r = 0.5, r=0.5, r(50)=0.5, beta=0.2, B=0.3, etc.
    patterns = [
        r"r\s*=\s*(-?\d+\.?\d*)",
        r"r\s*\(\s*\d+\s*\)\s*=\s*(-?\d+\.?\d*)",
        r"beta\s*=\s*(-?\d+\.?\d*)",
        r"B\s*=\s*(-?\d+\.?\d*)",
        r"coefficient\s*=\s*(-?\d+\.?\d*)",
        r"odds\s+ratio\s*=\s*(-?\d+\.?\d*)" # Often reported as OR, but we treat as effect
    ]
    
    values = []
    text_lower = text.lower()
    
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                val = float(match.group(1))
                # Heuristic confidence: if text contains "significant" or "p<", boost confidence
                confidence = 0.6
                if "significant" in text_lower or "p<" in text_lower or "p =" in text_lower:
                    confidence = 0.9
                # If value is between -1 and 1, likely r or beta
                if -10 < val < 10: 
                    values.append((val, confidence))
            except ValueError:
                continue
    
    return values

def select_median_closeness(values: List[Tuple[float, float]]) -> Optional[float]:
    """
    If multiple values found, select the one closest to the median of extracted values.
    """
    if not values:
        return None
    
    if len(values) == 1:
        return values[0][0]
    
    numeric_values = [v[0] for v in values]
    median_val = sum(numeric_values) / len(numeric_values)
    
    # Find value closest to median
    closest = min(values, key=lambda x: abs(x[0] - median_val))
    return closest[0]

def extract_study_metadata(abstract_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract structured metadata from an abstract entry.
    """
    pmid = abstract_data.get("pmid")
    text = abstract_data.get("abstract_text", "")
    
    if not text:
        return None

    # Extract effect size
    extracted = extract_effect_sizes(text)
    if not extracted:
        return None # Skip if no effect size found

    r_value = select_median_closeness(extracted)
    
    # Heuristic for n_samples: look for "n=" or "participants=" or "subjects="
    n_samples = None
    n_match = re.search(r"n\s*=\s*(\d+)", text, re.IGNORECASE)
    if n_match:
        n_samples = int(n_match.group(1))
    
    # Heuristic for p-value
    p_value = None
    p_match = re.search(r"p\s*[<>=]\s*([\d\.eE+-]+)", text, re.IGNORECASE)
    if p_match:
        try:
            p_value = float(p_match.group(1))
        except ValueError:
            pass

    # Determine pathway based on keywords
    text_lower = text.lower()
    pathway = "Unknown"
    if "scfa" in text_lower or "short-chain" in text_lower:
        pathway = "SCFA"
    elif "bdfn" in text_lower or "brain-derived" in text_lower:
        pathway = "BDNF"
    elif "hdac" in text_lower or "histone" in text_lower:
        pathway = "HDAC"
    elif "microbiome" in text_lower:
        pathway = "General Microbiome"

    # Determine effect direction
    effect_direction = "neutral"
    if r_value is not None:
        if r_value > 0.1:
            effect_direction = "positive"
        elif r_value < -0.1:
            effect_direction = "negative"

    return {
        "study_id": f"lit_{pmid}",
        "pmid": pmid,
        "n_samples": n_samples,
        "correlation_r": r_value,
        "p_value": p_value,
        "taxon_name": "Mixed/Unspecified", # Hard to extract specific taxa from abstract text reliably without NER model
        "pathway": pathway,
        "effect_direction": effect_direction,
        "abstract_text": text
    }

def main():
    """
    Main entry point for T040a.
    1. Search PubMed for PMIDs.
    2. Fetch abstracts.
    3. Extract effect sizes.
    4. Save to data/raw/literature_metadata.json.
    """
    logger.info("Starting Literature Extraction (T040a)...")
    
    # 1. Search
    pmids = search_pubmed_ids(PUBLISHED_QUERIES)
    if not pmids:
        logger.error("No PMIDs found. Cannot proceed.")
        # Create empty file to satisfy downstream dependencies, but log failure
        output_path = get_data_raw() / "literature_metadata.json"
        with open(output_path, 'w') as f:
            json.dump([], f, indent=2)
        return

    logger.info(f"Found {len(pmids)} unique PMIDs.")

    # 2. Fetch Abstracts
    abstracts = fetch_abstracts(pmids)
    logger.info(f"Successfully fetched {len(abstracts)} abstracts.")

    # 3. Process and Extract
    results = []
    confidence_scores = []
    
    for item in abstracts:
        metadata = extract_study_metadata(item)
        if metadata:
            results.append(metadata)
            # Collect confidence scores for logging
            extracted = extract_effect_sizes(item["abstract_text"])
            if extracted:
                # Take max confidence for logging
                confidence_scores.append(max([c for _, c in extracted]))

    # 4. Output
    output_dir = get_data_raw()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "literature_metadata.json"
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Saved {len(results)} studies to {output_path}")
    
    # Validation logging
    if confidence_scores:
        median_conf = sum(confidence_scores) / len(confidence_scores)
        logger.info(f"Number of extracted studies: {len(results)}")
        logger.info(f"Median confidence score: {median_conf:.4f}")
    else:
        logger.warning("No confidence scores extracted (no effect sizes found in abstracts).")

if __name__ == "__main__":
    main()
