import json
import logging
import os
import sys
from pathlib import Path

from code.data_search import search_geo_organism_stress

# Configure logging for the script execution
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/data_search.log')
    ]
)
logger = logging.getLogger(__name__)

def main():
    """
    Search GEO for Solanum herbivore-stress series.
    Outputs accession IDs to data/raw/geo_solanum_search.json.
    """
    # Define project root relative to this script location
    # The script is at code/run_geo_solanum_search.py
    project_root = Path(__file__).resolve().parent.parent
    output_dir = project_root / "data" / "raw"
    output_file = output_dir / "geo_solanum_search.json"

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Starting GEO search for Solanum herbivore-stress series...")

    try:
        # Perform the search using the existing utility
        # Organism: Solanum (covers tomato, potato, eggplant, etc.)
        # Stress type: herbivore
        results = search_geo_organism_stress(organism="Solanum", stress_type="herbivore")

        if not results:
            logger.warning("No results found for Solanum herbivore-stress.")
            output_data = {
                "query": {"organism": "Solanum", "stress_type": "herbivore"},
                "count": 0,
                "accession_ids": [],
                "status": "completed",
                "message": "No matching series found."
            }
        else:
            accession_ids = [r.get('accession') for r in results if r.get('accession')]
            logger.info(f"Found {len(accession_ids)} matching series.")
            
            output_data = {
                "query": {"organism": "Solanum", "stress_type": "herbivore"},
                "count": len(accession_ids),
                "accession_ids": accession_ids,
                "details": results,
                "status": "completed"
            }

        # Write results to JSON file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2)

        logger.info(f"Successfully wrote results to {output_file}")
        return 0

    except Exception as e:
        logger.error(f"Error during search: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
