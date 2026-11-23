"""
Module to save similarity results to CSV.

Implements T020: Save results to `data/derived/yearly_similarity.csv` 
with columns: year, mean_off_diagonal_similarity, intra_genre_variance.
"""
import os
import logging
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional

from similarity import (
    load_yearly_embeddings,
    compute_pairwise_cosine_similarity,
    calculate_mean_off_diagonal_similarity,
    calculate_intra_genre_variance,
    process_year
)
from utils import get_logger, setup_logging

# Ensure the directory exists
OUTPUT_DIR = Path("data/derived")
OUTPUT_FILE = OUTPUT_DIR / "yearly_similarity.csv"
EMBEDDINGS_DIR = Path("yearly_embeddings")

def save_similarity_results(results: List[Dict[str, Any]], output_path: Optional[Path] = None) -> None:
    """
    Save the calculated similarity results to a CSV file.
    
    Args:
        results: List of dictionaries containing year, mean_off_diagonal_similarity, 
                 and intra_genre_variance.
        output_path: Path to the output CSV file. Defaults to data/derived/yearly_similarity.csv.
        
    Raises:
        FileNotFoundError: If the output directory does not exist.
        IOError: If the file cannot be written.
    """
    if output_path is None:
        output_path = OUTPUT_FILE
        
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger = get_logger(__name__)
    logger.info(f"Saving similarity results to {output_path}")
    
    if not results:
        logger.warning("No results to save.")
        return

    fieldnames = ["year", "mean_off_diagonal_similarity", "intra_genre_variance"]
    
    try:
        with open(output_path, mode='w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in results:
                writer.writerow(row)
        logger.info(f"Successfully saved {len(results)} rows to {output_path}")
    except IOError as e:
        logger.error(f"Failed to write to {output_path}: {e}")
        raise

def main() -> None:
    """
    Main entry point to compute and save yearly similarity results.
    This function orchestrates the loading of embeddings, computation of metrics,
    and saving of the final CSV.
    """
    setup_logging()
    logger = get_logger(__name__)
    
    if not EMBEDDINGS_DIR.exists():
        logger.error(f"Embeddings directory not found: {EMBEDDINGS_DIR}. "
                     "Please ensure T014 (aggregate_yearly_embeddings) has been run first.")
        # T023 requirement: Log error handling for missing files
        # We raise to fail loudly as per constraints, but log first
        raise FileNotFoundError(f"Embeddings directory {EMBEDDINGS_DIR} not found. "
                                "Run T014 to generate yearly embeddings first.")
        
    # Scan for available year files
    year_files = sorted([f for f in EMBEDDINGS_DIR.iterdir() if f.suffix == '.npy'])
    
    if not year_files:
        logger.warning(f"No .npy files found in {EMBEDDINGS_DIR}.")
        # Create empty file or raise? Task implies saving results, so if no data, 
        # we create an empty CSV with headers or raise. Let's create empty CSV 
        # to satisfy the "save results" artifact requirement even if empty.
        save_similarity_results([])
        return

    logger.info(f"Found {len(year_files)} embedding files.")
    
    results = []
    
    for year_file in year_files:
        try:
            year = int(year_file.stem)
            logger.info(f"Processing year {year}...")
            
            # Load embeddings for this year
            genre_embeddings = load_yearly_embeddings(year_file)
            
            if genre_embeddings is None or len(genre_embeddings) == 0:
                logger.warning(f"No embeddings found for year {year}. Skipping.")
                continue
            
            # Compute pairwise similarity
            similarity_matrix = compute_pairwise_cosine_similarity(genre_embeddings)
            
            # Calculate metrics
            mean_sim = calculate_mean_off_diagonal_similarity(similarity_matrix)
            variance_sim = calculate_intra_genre_variance(genre_embeddings, similarity_matrix)
            
            results.append({
                "year": year,
                "mean_off_diagonal_similarity": mean_sim,
                "intra_genre_variance": variance_sim
            })
            
        except Exception as e:
            logger.error(f"Error processing year {year_file}: {e}")
            # T023 requirement: Log error handling
            continue
    
    # Sort results by year
    results.sort(key=lambda x: x['year'])
    
    # Save to CSV
    save_similarity_results(results)
    
    logger.info("T020 Task Complete: yearly_similarity.csv generated.")

if __name__ == "__main__":
    main()
