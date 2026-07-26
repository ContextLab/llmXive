import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

import requests

# Configure logging to stderr for immediate visibility
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# Metabolomics Workbench API endpoint
MW_API_URL = "https://www.metabolomicsworkbench.org/rest/v1/study/study_list"
MW_ANALYSIS_URL = "https://www.metabolomicsworkbench.org/rest/v1/analysis/analysis_list"

# Defense compound categories to search for
DEFENSE_CATEGORIES = [
    "terpenoid",
    "terpenoids",
    "alkaloid",
    "alkaloids",
    "phenylpropanoid",
    "phenylpropanoids",
    "defense",
    "stress",
    "herbivore",
    "insect"
]

def search_metabolomics_workbench(
    keywords: Optional[List[str]] = None,
    organism: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Search Metabolomics Workbench for studies related to plant defense compounds.

    Args:
        keywords: List of keywords to search for in study titles/abstracts
        organism: Optional organism filter (e.g., "Arabidopsis", "Solanum")

    Returns:
        List of study dictionaries with metadata
    """
    params = {
        "project_type": "METABOLOMICS",
        "data_type": "BOTH"
    }

    if keywords:
        # Combine keywords into a search string
        search_term = " ".join(keywords)
        params["search"] = search_term

    if organism:
        params["organism"] = organism

    logger.info(f"Searching Metabolomics Workbench with params: {params}")

    try:
        response = requests.get(MW_API_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        studies = data.get("STUDY", [])
        logger.info(f"Found {len(studies)} studies from Metabolomics Workbench")

        # Filter for relevant studies
        relevant_studies = []
        for study in studies:
            title = study.get("STUDY_TITLE", "").lower()
            abstract = study.get("ABSTRACT", "").lower()
            organism_name = study.get("ORGANISM", "").lower()

            # Check if study mentions defense compounds or related terms
            is_relevant = False
            for category in DEFENSE_CATEGORIES:
                if category in title or category in abstract:
                    is_relevant = True
                    break

            # Also check if organism matches (if specified)
            if organism and organism.lower() not in organism_name:
                continue

            if is_relevant:
                relevant_studies.append(study)

        logger.info(f"Filtered to {len(relevant_studies)} relevant studies")
        return relevant_studies

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to search Metabolomics Workbench: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Metabolomics Workbench response: {e}")
        raise

def search_by_analysis_type(
    study_id: str,
    analysis_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get analysis details for a specific study.

    Args:
        study_id: Metabolomics Workbench study ID (e.g., ST000001)
        analysis_type: Optional filter for analysis type

    Returns:
        List of analysis dictionaries
    """
    params = {
        "study_id": study_id
    }

    if analysis_type:
        params["analysis_type"] = analysis_type

    logger.info(f"Fetching analyses for study {study_id}")

    try:
        response = requests.get(MW_ANALYSIS_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        analyses = data.get("ANALYSIS", [])
        logger.info(f"Found {len(analyses)} analyses for study {study_id}")

        return analyses

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch analyses for study {study_id}: {e}")
        raise

def save_search_results(
    results: List[Dict[str, Any]],
    output_path: Path
) -> None:
    """
    Save search results to a JSON file.

    Args:
        results: List of study dictionaries
        output_path: Path to output file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved {len(results)} results to {output_path}")

def main():
    """
    Main entry point for Metabolomics Workbench search.
    Searches for defense compound experiments and saves results.
    """
    # Define output path
    base_path = Path("projects/PROJ-503-predicting-plant-defense-compound-produc")
    output_dir = base_path / "data" / "raw"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "metabolomics_workbench_defense_studies.json"

    logger.info("Starting Metabolomics Workbench search for defense compounds...")

    try:
        # Search for defense-related studies
        # Search broadly first, then filter
        all_results = []

        # Search for terpenoids
        terpenoid_results = search_metabolomics_workbench(
            keywords=["terpenoid", "defense", "plant"]
        )
        all_results.extend(terpenoid_results)

        # Search for alkaloids
        alkaloid_results = search_metabolomics_workbench(
            keywords=["alkaloid", "defense", "plant"]
        )
        all_results.extend(alkaloid_results)

        # Search for phenylpropanoids
        phenylpropanoid_results = search_metabolomics_workbench(
            keywords=["phenylpropanoid", "defense", "plant"]
        )
        all_results.extend(phenylpropanoid_results)

        # Search for herbivore stress
        herbivore_results = search_metabolomics_workbench(
            keywords=["herbivore", "insect", "stress", "plant"]
        )
        all_results.extend(herbivore_results)

        # Deduplicate by study ID
        unique_studies = {}
        for study in all_results:
            study_id = study.get("STUDY_ID")
            if study_id and study_id not in unique_studies:
                unique_studies[study_id] = study

        final_results = list(unique_studies.values())
        logger.info(f"Total unique relevant studies: {len(final_results)}")

        # Log details of found studies
        for study in final_results[:10]:  # Log first 10
            logger.info(f"  - {study.get('STUDY_ID')}: {study.get('STUDY_TITLE', 'No title')[:80]}")

        if len(final_results) > 10:
            logger.info(f"  ... and {len(final_results) - 10} more")

        # Save results
        save_search_results(final_results, output_file)

        # Also create a summary CSV for quick reference
        summary_path = output_dir / "metabolomics_workbench_defense_studies_summary.csv"
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("study_id,title,organism,platform,public_date\n")
            for study in final_results:
                study_id = study.get("STUDY_ID", "")
                title = study.get("STUDY_TITLE", "").replace("\n", " ").replace(",", " ")
                organism = study.get("ORGANISM", "")
                platform = study.get("DATA_PROCESSING_PLATFORM", "")
                public_date = study.get("PUBLIC_RELEASE_DATE", "")

                f.write(f"{study_id},{title},{organism},{platform},{public_date}\n")

        logger.info(f"Search complete. Results saved to {output_file}")
        logger.info(f"Summary saved to {summary_path}")

        # Return success
        return 0

    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise

if __name__ == "__main__":
    sys.exit(main())
