"""
Module to save similarity results to CSV.
Implements T020: Save results to data/derived/yearly_similarity.csv
with columns: year, mean_off_diagonal_similarity, intra_genre_variance
"""
import os
import logging
import csv
from pathlib import Path
from typing import List, Dict, Any

# Import from existing API surface
from similarity import (
    load_yearly_embeddings,
    compute_pairwise_cosine_similarity,
    calculate_mean_off_diagonal_similarity,
    calculate_intra_genre_variance,
    process_year
)
from utils import get_logger, setup_logging

# Ensure project root paths are correct
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DERIVED_DIR = PROJECT_ROOT / "data" / "derived"
EMBEDDINGS_DIR = PROJECT_ROOT / "yearly_embeddings"
OUTPUT_FILE = DATA_DERIVED_DIR / "yearly_similarity.csv"

def save_similarity_results(results: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save similarity calculation results to a CSV file.
    
    Args:
        results: List of dictionaries containing year, mean_off_diagonal_similarity, 
                and intra_genre_variance
        output_path: Path to the output CSV file
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Define CSV columns
    fieldnames = ['year', 'mean_off_diagonal_similarity', 'intra_genre_variance']
    
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for result in results:
            writer.writerow({
                'year': result['year'],
                'mean_off_diagonal_similarity': result['mean_off_diagonal_similarity'],
                'intra_genre_variance': result['intra_genre_variance']
            })
    
    logging.info(f"Similarity results saved to {output_path}")

def main():
    """
    Main entry point for T020: Load yearly embeddings, compute similarities,
    and save results to CSV.
    """
    # Setup logging
    setup_logging()
    logger = get_logger(__name__)
    
    logger.info("Starting similarity results generation (T020)")
    
    # Ensure embeddings directory exists
    if not EMBEDDINGS_DIR.exists():
        logger.error(f"Embeddings directory not found: {EMBEDDINGS_DIR}")
        logger.error("Please run the embeddings pipeline first to generate yearly embeddings.")
        return 1
    
    # Get list of available years
    embedding_files = list(EMBEDDINGS_DIR.glob("*.npy"))
    if not embedding_files:
        logger.error(f"No embedding files found in {EMBEDDINGS_DIR}")
        return 1
    
    logger.info(f"Found {len(embedding_files)} embedding files")
    
    # Process each year and collect results
    results = []
    
    for embedding_file in sorted(embedding_files):
        try:
            year_str = embedding_file.stem
            year = int(year_str)
            
            logger.info(f"Processing year {year}...")
            
            # Load embeddings for this year
            genre_vectors = load_yearly_embeddings(EMBEDDINGS_DIR, year)
            
            if genre_vectors is None or len(genre_vectors) == 0:
                logger.warning(f"No valid embeddings for year {year}, skipping")
                continue
            
            # Compute pairwise cosine similarity
            similarity_matrix = compute_pairwise_cosine_similarity(genre_vectors)
            
            # Calculate statistics
            mean_sim = calculate_mean_off_diagonal_similarity(similarity_matrix)
            variance_sim = calculate_intra_genre_variance(genre_vectors)
            
            # Store result
            results.append({
                'year': year,
                'mean_off_diagonal_similarity': float(mean_sim),
                'intra_genre_variance': float(variance_sim)
            })
            
            logger.info(f"Year {year}: mean_sim={mean_sim:.4f}, variance={variance_sim:.4f}")
            
        except Exception as e:
            logger.error(f"Error processing year {year_str}: {e}")
            continue
    
    if not results:
        logger.error("No results to save")
        return 1
    
    # Sort results by year
    results.sort(key=lambda x: x['year'])
    
    # Save to CSV
    save_similarity_results(results, OUTPUT_FILE)
    
    logger.info(f"Successfully processed {len(results)} years")
    logger.info(f"Output saved to: {OUTPUT_FILE}")
    
    return 0

if __name__ == "__main__":
    exit(main())