import os
import sys
import csv
import logging
import math
from pathlib import Path

# Configure logging to stdout and file if needed
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Ensure project structure paths are available relative to script location
# Assuming script runs from project root or code/ directory
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SCREENING_DIR = DATA_DIR / "screening"

# Ensure directories exist
SCREENING_DIR.mkdir(parents=True, exist_ok=True)

SCREENING_LOG_PATH = SCREENING_DIR / "screening_log.csv"
ADJUDICATION_REQUEST_PATH = SCREENING_DIR / "adjudication_request.csv"

def load_screening_log(path: Path = None) -> list:
    """
    Loads the screening log CSV.
    Expected columns: study_id, reviewer_1_decision, reviewer_2_decision, ...
    """
    if path is None:
        path = SCREENING_LOG_PATH
    
    if not path.exists():
        logger.error(f"Screening log not found at {path}. Cannot calculate Kappa.")
        sys.exit(1)
    
    studies = []
    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            studies.append(row)
    
    return studies

def calculate_cohen_kappa(studies: list) -> tuple:
    """
    Calculates Cohen's Kappa for two reviewers based on 'reviewer_1_decision' and 'reviewer_2_decision'.
    
    Returns:
        (kappa, disagreements): Tuple of float (kappa) and list of dicts (disputed studies).
    """
    if not studies:
        logger.warning("No studies found in screening log. Kappa cannot be calculated.")
        return 0.0, []

    n = len(studies)
    agreements = 0
    disagreements = []

    # Count observed agreement (Po)
    for study in studies:
        r1 = study.get('reviewer_1_decision', '').strip().lower()
        r2 = study.get('reviewer_2_decision', '').strip().lower()
        
        # Skip rows with missing data for kappa calculation
        if not r1 or not r2:
            continue

        if r1 == r2:
            agreements += 1
        else:
            disagreements.append(study)

    if agreements + len(disagreements) == 0:
        # All missing or invalid
        return 0.0, []

    po = agreements / (agreements + len(disagreements))

    # Calculate expected agreement (Pe)
    # We need the marginal probabilities
    # Let's assume binary decisions: 'include' vs 'exclude' (or similar)
    # Count occurrences for each decision
    r1_counts = {}
    r2_counts = {}
    
    for study in studies:
        r1 = study.get('reviewer_1_decision', '').strip().lower()
        r2 = study.get('reviewer_2_decision', '').strip().lower()
        
        if not r1 or not r2:
            continue
        
        r1_counts[r1] = r1_counts.get(r1, 0) + 1
        r2_counts[r2] = r2_counts.get(r2, 0) + 1

    total_valid = agreements + len(disagreements)
    
    pe = 0.0
    all_decisions = set(r1_counts.keys()) | set(r2_counts.keys())
    
    for decision in all_decisions:
        p_r1 = r1_counts.get(decision, 0) / total_valid
        p_r2 = r2_counts.get(decision, 0) / total_valid
        pe += p_r1 * p_r2

    if pe == 1.0:
        kappa = 1.0
    else:
        kappa = (po - pe) / (1 - pe)
    
    return kappa, disagreements

def generate_adjudication_request(disputed_studies: list, path: Path = None) -> None:
    """
    Writes the list of disputed studies to the adjudication request CSV.
    """
    if path is None:
        path = ADJUDICATION_REQUEST_PATH
    
    if not disputed_studies:
        logger.info("No disputes found. No adjudication request file generated.")
        return

    logger.warning(f"Found {len(disputed_studies)} disputed studies. Generating adjudication request.")
    
    # Determine fields from the first study, ensuring we include necessary keys
    if disputed_studies:
        fieldnames = list(disputed_studies[0].keys())
        # Ensure specific columns for adjudication if missing
        if 'dispute_reason' not in fieldnames:
            fieldnames.append('dispute_reason')
        
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for study in disputed_studies:
                # Add a generic reason if not present, though usually logic implies the conflict
                study_copy = study.copy()
                study_copy['dispute_reason'] = "Conflicting reviewer decisions"
                writer.writerow(study_copy)
        
        logger.info(f"Adjudication request written to {path}")
    else:
        logger.warning("Disputed studies list is empty, cannot write file.")

def main():
    """
    Main entry point for T016: Cohen's Kappa calculation and adjudication handling.
    """
    logger.info("Starting Cohen's Kappa calculation (Task T016)...")
    
    # 1. Load data
    studies = load_screening_log()
    
    if not studies:
        logger.error("Screening log is empty or missing. Halting.")
        sys.exit(1)

    # 2. Calculate Kappa
    kappa, disputes = calculate_cohen_kappa(studies)
    
    logger.info(f"Cohen's Kappa calculated: {kappa:.4f}")
    
    # 3. Check threshold
    THRESHOLD = 0.6
    
    if kappa < THRESHOLD:
        msg = f"Human Adjudication Required (Kappa < {THRESHOLD})"
        logger.error(msg)
        
        # 4. Generate adjudication request
        generate_adjudication_request(disputes)
        
        # 5. Exit with code 1 (HALT)
        logger.error("HALT: Waiting for human adjudication.")
        sys.exit(1)
    else:
        logger.info(f"Kappa ({kappa:.4f}) >= {THRESHOLD}. Adjudication not required. Proceeding.")
        sys.exit(0)

if __name__ == "__main__":
    main()