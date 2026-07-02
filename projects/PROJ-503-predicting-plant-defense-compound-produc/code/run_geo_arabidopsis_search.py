"""
Script to search GEO for Arabidopsis herbivore-stress series.
Outputs results to data/raw/geo_arabidopsis_search.json.
"""
import json
import logging
import os
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.data_search import search_geo_organism_stress

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    # Define output path
    data_dir = project_root / "data" / "raw"
    data_dir.mkdir(parents=True, exist_ok=True)
    output_file = data_dir / "geo_arabidopsis_search.json"

    logger.info(f"Preparing to search GEO for Arabidopsis herbivore stress studies.")
    logger.info(f"Output will be written to: {output_file}")

    # Define search parameters based on T001 specs
    organism = "Arabidopsis thaliana"
    # Herbivore stress keywords
    herbivore_keywords = [
        "herbivore", "insect", "feeding", "chewing", "sucking",
        "aphid", "caterpillar", "moth", "beetle", "fly"
    ]

    try:
        # Execute search
        results = search_geo_organism_stress(
            organism=organism,
            stress_keywords=herbivore_keywords,
            retmax=200
        )

        if not results:
            logger.warning("No results found. This might indicate a network issue or no matching studies.")
            # Write empty list to file to indicate search was attempted but returned nothing
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({"query": f"{organism} herbivore stress", "results": [], "count": 0}, f, indent=2)
            return

        # Format output
        output_data = {
            "query": f"{organism} AND ({' OR '.join(herbivore_keywords)})",
            "organism": organism,
            "search_type": "herbivore_stress",
            "count": len(results),
            "results": results
        }

        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Successfully found {len(results)} series.")
        logger.info(f"Results written to {output_file}")
        
        # Log first few accession IDs for quick verification
        if results:
            accessions = [r['accession'] for r in results[:5]]
            logger.info(f"Sample accessions: {', '.join(accessions)}")

    except Exception as e:
        logger.error(f"Search failed with error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
