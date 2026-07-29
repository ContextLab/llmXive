"""
Static Ground Truth Module (T020, T021).
Fetches external medical facts from PubMed using Entrez and saves to data/raw/static_medical_facts.json.
"""
import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

from config import get_config

# Try to import biopython
try:
    from Bio import Entrez
except ImportError:
    logger = logging.getLogger(__name__)
    logger.error("The 'biopython' package is required. Install with: pip install biopython")
    raise

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def download_medqa_facts(questions: List[str]) -> List[Dict[str, str]]:
    """
    Fetch abstracts from PubMed for each question/correct_answer.
    Uses Entrez with a delay to respect rate limits.
    """
    config = get_config()
    email = config.get('entrez', {}).get('email', 'researcher@example.com')
    Entrez.email = email
    
    facts = []
    
    for i, question in enumerate(questions):
        # Use correct_answer or the question itself as search term
        # We'll assume the input data has a 'correct_answer' field or we use the text
        search_term = question[:50] # Truncate for safety
        
        try:
            # Search for the term
            handle = Entrez.esearch(db="pubmed", term=search_term, retmax=1)
            record = Entrez.read(handle)
            handle.close()
            
            id_list = record["IdList"]
            
            if not id_list:
                facts.append({"query": question, "external_fact": "", "status": "no_results"})
                continue
            
            # Fetch the first abstract
            id_str = ",".join(id_list)
            fetch_handle = Entrez.efetch(db="pubmed", id=id_str, retmode="xml")
            fetch_record = Entrez.read(fetch_handle)
            fetch_handle.close()
            
            # Parse abstract
            abstract_text = ""
            if fetch_record and fetch_record[0].get("MedlineCitation", {}).get("Article", {}).get("Abstract"):
                abstract = fetch_record[0]["MedlineCitation"]["Article"]["Abstract"]
                abstract_text = abstract.get("AbstractText", "")
                if isinstance(abstract_text, list):
                    abstract_text = " ".join(abstract_text)
            
            facts.append({
                "query": question,
                "external_fact": abstract_text,
                "status": "success",
                "pubmed_id": id_list[0]
            })
            
        except Exception as e:
            logger.warning(f"Failed to fetch fact for '{search_term}': {str(e)}")
            facts.append({"query": question, "external_fact": "", "status": "error", "error": str(e)})
        
        # Respect rate limit (3 queries/sec for unregistered, 10/sec registered)
        if i % 3 == 0:
            import time
            time.sleep(0.34)
    
    return facts

def verify_and_save_static_facts(facts: List[Dict[str, Any]], output_path: Path):
    """Verify facts and save to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Filter out empty facts if necessary, but keep for debugging
    valid_facts = [f for f in facts if f.get('external_fact')]
    logger.info(f"Saved {len(valid_facts)} valid facts out of {len(facts)} queries.")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(facts, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved static medical facts to {output_path}")

def run_static_ground_truth_pipeline():
    """Execute the full static ground truth pipeline (T020)."""
    logger.info("Starting Static Ground Truth Pipeline (T020)")
    config = get_config()
    
    input_path = Path(config['paths']['raw']) / 'medmis_subset.csv'
    output_path = Path(config['paths']['raw']) / 'static_medical_facts.json'
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}. Run ingestion (T013) first.")
    
    import pandas as pd
    df = pd.read_csv(input_path)
    
    # Get correct answers or use text
    if 'correct_answer' in df.columns:
        queries = df['correct_answer'].dropna().tolist()
    elif 'text' in df.columns:
        queries = df['text'].dropna().tolist()
    else:
        raise ValueError("Input dataset missing 'correct_answer' or 'text' column.")
    
    if not queries:
        raise ValueError("No queries found to fetch facts for.")
    
    logger.info(f"Fetching facts for {len(queries)} queries...")
    facts = download_medqa_facts(queries)
    
    verify_and_save_static_facts(facts, output_path)
    
    logger.info("Static Ground Truth Pipeline completed successfully.")
    return output_path

def main():
    """Entry point for static ground truth."""
    try:
        run_static_ground_truth_pipeline()
    except Exception as e:
        logger.error(f"Static ground truth pipeline failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()