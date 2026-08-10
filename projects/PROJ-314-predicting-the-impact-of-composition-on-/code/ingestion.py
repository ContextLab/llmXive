import pandas as pd
import logging
import re
import json
from pathlib import Path
from urllib.parse import urlparse
import arxiv
import pdfplumber
import tempfile
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for extraction
COMPOSITION_PATTERN = re.compile(r"(Al|Si|O|Ti|Zr|Zn|Nb|Ta|Hf|Mo|W|V|Cr|Mn|Fe|Co|Ni|Cu|Ga|In|Sn|Sb|Te|Bi|Pb|S|Se|F|Cl|Br|I)")
TARGET_PATTERN = re.compile(r"(Weibull|Modulus)")

def fetch_arxiv_data():
    """
    Fetches ceramic Weibull data from arXiv.
    1. Searches for 'all:ceramic AND all:weibull'.
    2. Downloads the top 5 PDFs (sorted by relevance).
    3. Extracts the first valid table found in each PDF.
    4. Filters rows based on regex patterns for composition and target.
    5. Saves raw data to data/raw/arxiv_raw.json.
    
    Raises:
        RuntimeError: If fetch fails, no PDFs are found, or extraction yields no valid data.
    """
    logger.info("Starting arXiv data fetch...")
    
    # 1. Search arXiv
    client = arxiv.Client()
    search = arxiv.Search(
        query="all:ceramic AND all:weibull",
        max_results=5,
        sort_by=arxiv.SortCriterion.Relevance
    )
    
    results = list(client.results(search))
    if not results:
        raise RuntimeError("No arXiv results found for 'all:ceramic AND all:weibull'.")
    
    logger.info(f"Found {len(results)} arXiv results. Processing top 5.")
    
    all_rows = []
    extracted_count = 0
    
    for i, result in enumerate(results):
        logger.info(f"Processing result {i+1}/{len(results)}: {result.title}")
        
        pdf_path = None
        try:
            # Download PDF to a temporary file
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                pdf_path = tmp.name
            
            # Use arxiv client to download
            result.download_pdf(filename=pdf_path)
            
            # 2. Extract tables from PDF
            pdf_rows = []
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    tables = page.extract_tables()
                    if tables:
                        # Take the first valid table found
                        table = tables[0]
                        if table:
                            for row in table:
                                if row is None:
                                    continue
                                # Clean row data
                                cleaned_row = [str(cell).strip() if cell else "" for cell in row]
                                pdf_rows.append(cleaned_row)
                            break # Only first valid table
            
            # 3. Parse and filter rows
            # Assuming the table has headers or we need to guess structure.
            # We look for rows containing both composition elements and Weibull/Modulus keywords.
            
            for row in pdf_rows:
                row_text = " ".join(row).lower()
                
                # Check for target keyword
                if not TARGET_PATTERN.search(row_text):
                    continue
                
                # Check for composition elements
                if not COMPOSITION_PATTERN.search(row_text):
                    continue
                
                # Attempt to extract composition and value
                # Heuristic: Look for a string that looks like a composition (e.g., Al2O3) and a number
                composition_candidate = None
                value_candidate = None
                
                # Simple heuristic: find the first element sequence and the first number sequence
                # This is a simplification; real parsing might need more robust logic
                # But per task: "Extract the first valid table found... use regex patterns"
                # We will try to construct a row if the text matches the patterns.
                
                # Let's try to find a composition string like "Al2O3" or "Al: 2 O: 3"
                # For now, we will store the raw row text if it passes the filter, 
                # and try to parse specific columns if the table structure is clear.
                # Since table structure varies wildly, we will store the row as a dict 
                # if we can identify a composition-like string and a number-like string.
                
                # Re-scan row for specific patterns
                comp_match = COMPOSITION_PATTERN.search(" ".join(row))
                target_match = TARGET_PATTERN.search(" ".join(row))
                
                if comp_match and target_match:
                    # Try to find a number (Weibull modulus)
                    numbers = re.findall(r"\d+\.?\d*", " ".join(row))
                    if numbers:
                        # Assume the first number is the modulus if it's reasonable, 
                        # or the last one. Let's pick the first one > 1.0 and < 100.
                        found_val = None
                        for n_str in numbers:
                            try:
                                val = float(n_str)
                                if 1.0 <= val <= 100.0:
                                    found_val = val
                                    break
                            except ValueError:
                                continue
                        
                        if found_val is not None:
                            # Extract the composition string roughly
                            # Join elements found in the row
                            comp_str = comp_match.group(0)
                            # Look for surrounding context to build a better comp string if possible
                            # For now, use the matched element as a placeholder or the whole row text if it looks like a formula
                            # Better: look for a sequence of letters and numbers
                            full_comp = re.search(r"([A-Z][a-z]?[0-9]*\s*)+", " ".join(row))
                            if full_comp:
                                comp_str = full_comp.group(0).strip()
                            
                            entry = {
                                "source": "arxiv",
                                "title": result.title,
                                "arxiv_id": result.entry_id,
                                "composition": comp_str,
                                "weibull_modulus": found_val,
                                "raw_row": row
                            }
                            all_rows.append(entry)
                            extracted_count += 1
        
        except Exception as e:
            logger.warning(f"Failed to process PDF for {result.title}: {e}")
        finally:
            if pdf_path and os.path.exists(pdf_path):
                try:
                    os.remove(pdf_path)
                except:
                    pass
    
    if extracted_count == 0:
        raise RuntimeError("No valid tables with Weibull/Modulus and composition data found in the top 5 arXiv PDFs.")
    
    # 4. Save to data/raw/arxiv_raw.json
    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "arxiv_raw.json"
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_rows, f, indent=4)
    
    logger.info(f"Successfully extracted {extracted_count} entries to {output_path}")
    return all_rows

if __name__ == '__main__':
    fetch_arxiv_data()
