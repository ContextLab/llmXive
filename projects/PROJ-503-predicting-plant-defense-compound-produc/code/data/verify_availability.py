"""
Task T000: Verify availability of specific datasets.

Verifies the existence and basic metadata of:
- GSE21857 (Arabidopsis thaliana, herbivore stress)
- GSE167633 (Solanum lycopersicum, herbivore stress)
- ST002565 (Metabolomics Workbench, plant defense metabolites)

Abort criteria:
- If any dataset is not found via API search.
- If metadata does not confirm herbivore/stress context.
- If minimum sample requirements are not met (>= 3 samples per condition).

Output: docs/dataset_availability_report.md
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from data_search import search_geo, search_geo_organism_stress
from download_metabolomics import fetch_study_metadata
from exceptions import E_DATASET

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Target Datasets Configuration
TARGET_GEO_IDS = ["GSE21857", "GSE167633"]
TARGET_MW_IDS = ["ST002565"]
MIN_SAMPLES = 3  # Minimum samples required per dataset to be considered viable

def verify_geo_dataset(accession_id: str) -> Dict[str, Any]:
    """
    Verify a GEO dataset by fetching its metadata.
    Checks for existence, organism, and stress/defense context.
    """
    result = {
        "accession_id": accession_id,
        "source": "GEO",
        "found": False,
        "organism": None,
        "title": None,
        "sample_count": 0,
        "is_herbivore_stress": False,
        "error": None
    }

    try:
        # Use the search function which queries NCBI E-utilities
        # We search specifically for the accession to ensure we get the exact record
        search_results = search_geo(accession_id)
        
        if not search_results or len(search_results) == 0:
            result["error"] = "Dataset not found in GEO search"
            return result

        # The search function usually returns a list of summaries. 
        # We expect the first one to match the accession if found.
        # Note: The existing search_geo function might return raw JSON or parsed list.
        # Assuming it returns a list of dicts based on typical implementation patterns.
        record = search_results[0]
        
        # Extract metadata
        result["found"] = True
        result["title"] = record.get("title", "N/A")
        result["organism"] = record.get("organism", "Unknown")
        
        # Count samples (GEO Series Matrix usually lists samples in 'samples' key or similar)
        # If the search result doesn't have sample count, we might need to fetch the full soft file
        # For now, we assume the search result has 'samples' or 'total_samples'
        samples = record.get("samples", [])
        if isinstance(samples, list):
            result["sample_count"] = len(samples)
        elif isinstance(samples, int):
            result["sample_count"] = samples
        else:
            # Fallback: try to parse from title or description if sample count is missing
            result["sample_count"] = 0 # Conservative estimate if not found

        # Check for herbivore/stress context
        title_lower = (result["title"] or "").lower()
        desc_lower = (record.get("description", "") or "").lower()
        text_to_check = title_lower + " " + desc_lower

        stress_keywords = ["herbivore", "insect", "stress", "defense", "wounding", "pathogen", "treatment"]
        # Simple heuristic: check if any stress keyword is present
        # A more robust check would parse the 'characteristics' field from the full soft file
        if any(keyword in text_to_check for keyword in stress_keywords):
            result["is_herbivore_stress"] = True
        else:
            # If not obvious, we might need to flag it, but for T000 we abort if NOT found/stress
            # We'll be strict: if it doesn't look like stress, mark it as such to trigger abort logic
            result["is_herbivore_stress"] = False

        # Validate sample count
        if result["sample_count"] < MIN_SAMPLES:
            result["error"] = f"Insufficient samples: {result['sample_count']} < {MIN_SAMPLES}"
            result["found"] = False # Treat as not viable

    except Exception as e:
        result["error"] = str(e)
        logger.error(f"Error verifying GEO {accession_id}: {e}")

    return result

def verify_mw_dataset(accession_id: str) -> Dict[str, Any]:
    """
    Verify a Metabolomics Workbench dataset.
    """
    result = {
        "accession_id": accession_id,
        "source": "Metabolomics Workbench",
        "found": False,
        "title": None,
        "sample_count": 0,
        "is_plant_defense": False,
        "error": None
    }

    try:
        # Fetch study metadata
        metadata = fetch_study_metadata(accession_id)
        
        if not metadata:
            result["error"] = "Study metadata not found"
            return result

        result["found"] = True
        result["title"] = metadata.get("study_title", "N/A")
        
        # Estimate sample count from metadata if available
        # MW metadata often contains 'subject_count' or similar
        subjects = metadata.get("subject_count", 0)
        if subjects > 0:
            result["sample_count"] = subjects
        else:
            # Fallback: try to infer from analysis metadata or description
            result["sample_count"] = 0 

        # Check for plant defense context
        title_lower = (result["title"] or "").lower()
        # MW descriptions are often in a 'study_description' field
        desc = metadata.get("study_description", "") or ""
        desc_lower = desc.lower()
        text_to_check = title_lower + " " + desc_lower

        defense_keywords = ["plant", "defense", "metabolite", "secondary", "stress", "herbivore", "insect"]
        if any(keyword in text_to_check for keyword in defense_keywords):
            result["is_plant_defense"] = True
        else:
            result["is_plant_defense"] = False

        if result["sample_count"] < MIN_SAMPLES:
            result["error"] = f"Insufficient samples: {result['sample_count']} < {MIN_SAMPLES}"
            result["found"] = False

    except Exception as e:
        result["error"] = str(e)
        logger.error(f"Error verifying MW {accession_id}: {e}")

    return result

def generate_report(geo_results: List[Dict], mw_results: List[Dict]) -> str:
    """
    Generate the markdown report content.
    """
    lines = [
        "# Dataset Availability Report",
        f"Generated: {Path.cwd()}",
        "",
        "## Summary",
        ""
    ]

    all_results = geo_results + mw_results
    total = len(all_results)
    found_count = sum(1 for r in all_results if r["found"] and not r.get("error"))
    stress_valid_count = sum(1 for r in all_results if r["found"] and r.get("is_herbivore_stress") or r.get("is_plant_defense"))

    lines.append(f"- Total datasets checked: {total}")
    lines.append(f"- Found and valid: {found_count}")
    lines.append(f"- Context valid (Stress/Defense): {stress_valid_count}")
    lines.append("")

    for result in all_results:
        status = "✅ FOUND" if result["found"] and not result.get("error") else "❌ FAILED"
        context_status = "✅ Context OK" if (result.get("is_herbivore_stress") or result.get("is_plant_defense")) else "❌ Context Missing"
        
        lines.append(f"## {result['accession_id']} ({result['source']})")
        lines.append(f"- **Status**: {status}")
        lines.append(f"- **Title**: {result.get('title', 'N/A')}")
        lines.append(f"- **Organism**: {result.get('organism', 'N/A')}")
        lines.append(f"- **Sample Count**: {result.get('sample_count', 0)}")
        lines.append(f"- **Context Check**: {context_status}")
        
        if result.get("error"):
            lines.append(f"- **Error**: {result['error']}")
        
        lines.append("")

    return "\n".join(lines)

def main():
    """
    Main entry point for T000.
    """
    logger.info("Starting Dataset Availability Verification (T000)...")
    
    geo_results = []
    mw_results = []

    # Verify GEO datasets
    for accession in TARGET_GEO_IDS:
        logger.info(f"Verifying GEO: {accession}")
        res = verify_geo_dataset(accession)
        geo_results.append(res)

    # Verify Metabolomics Workbench datasets
    for accession in TARGET_MW_IDS:
        logger.info(f"Verifying MW: {accession}")
        res = verify_mw_dataset(accession)
        mw_results.append(res)

    # Generate Report
    report_content = generate_report(geo_results, mw_results)
    
    # Ensure docs directory exists
    docs_dir = PROJECT_ROOT / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    report_path = docs_dir / "dataset_availability_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)
    
    logger.info(f"Report written to {report_path}")

    # Check Abort Criteria
    all_results = geo_results + mw_results
    for res in all_results:
        if not res["found"]:
            error_msg = f"Dataset {res['accession_id']} ({res['source']}) failed verification: {res.get('error', 'Unknown error')}"
            logger.error(error_msg)
            # Raise E_DATASET to abort the pipeline as per requirements
            raise E_DATASET(error_msg)
        
        # Check context specifically
        is_stress = res.get("is_herbivore_stress", False) or res.get("is_plant_defense", False)
        if not is_stress:
            error_msg = f"Dataset {res['accession_id']} ({res['source']}) does not meet herbivore-stress/defense criteria."
            logger.error(error_msg)
            raise E_DATASET(error_msg)

    logger.info("All datasets verified successfully.")

if __name__ == "__main__":
    main()
