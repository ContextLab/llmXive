import json
import logging
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_file_text(file_path: Path) -> str:
    """Load and return the text content of a file."""
    if not file_path.exists():
        raise FileNotFoundError(f"Required file not found: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def extract_terms(text: str) -> List[str]:
    """Extract key terms (data sources, metrics) from text for comparison."""
    # Simple regex to find potential data source names or specific requirements
    # Looking for patterns like "NOAA", "PRISM", "Daymet", "eBird", "FR-001"
    patterns = [
        r'\b(NOAA|PRISM|Daymet|eBird|CLO|Cornell)\b',
        r'FR-\d+',
        r'SC-\d+',
        r'US\d+'
    ]
    terms = set()
    for pattern in patterns:
        terms.update(re.findall(pattern, text, re.IGNORECASE))
    return list(terms)

def check_mandatory_a_priori_gp(plan_terms: List[str], spec_terms: List[str]) -> Optional[str]:
    """Check for contradictions regarding Mandatory GP (if any)."""
    # If spec says mandatory GP but plan says optional or none
    if "GP" in spec_terms and "GP" in plan_terms:
        # This is a placeholder logic; in a real scenario, we'd parse the context
        # For now, we assume if both mention it, we check for "Mandatory" keyword
        pass
    return None

def check_critical_data_scope_note(plan_terms: List[str], spec_terms: List[str]) -> Optional[str]:
    """Check for contradictions regarding data scope (e.g., 2020-2024)."""
    # Look for year ranges
    plan_years = re.findall(r'(\d{4}-\d{4})', load_file_text(Path("plan.md")))
    spec_years = re.findall(r'(\d{4}-\d{4})', load_file_text(Path("specs/001-bird-migration-climate-correlation/spec.md")))
    
    if plan_years and spec_years and plan_years[0] != spec_years[0]:
        return f"Year range mismatch: Plan has {plan_years[0]}, Spec has {spec_years[0]}"
    return None

def check_data_source_mismatch(plan_terms: List[str], spec_terms: List[str]) -> Optional[str]:
    """Check for contradictions in data sources (e.g., NOAA vs Daymet)."""
    # Spec usually demands NOAA/PRISM (FR-001)
    # Plan might substitute if unavailable
    if "NOAA" in spec_terms and "NOAA" not in plan_terms and "Daymet" in plan_terms:
        # This might be a deviation, check whitelist later
        return "Data source mismatch: Spec requires NOAA, Plan uses Daymet (check whitelist)"
    if "eBird" in spec_terms and "eBird" not in plan_terms:
        return "Data source mismatch: Spec requires eBird, Plan missing eBird reference"
    return None

def check_unknown_terms(plan_terms: List[str], spec_terms: List[str]) -> Optional[str]:
    """Check for terms in spec not found in plan."""
    # Simple check: if a critical term in spec is missing in plan
    critical_terms = ["eBird", "NOAA", "PRISM", "Daymet", "CLO"]
    missing = []
    for term in critical_terms:
        if term in spec_terms and term not in plan_terms:
            missing.append(term)
    if missing:
        return f"Critical terms in spec missing from plan: {', '.join(missing)}"
    return None

def verify_alignment() -> Dict[str, Any]:
    """
    Main logic to verify alignment between plan.md and spec.md.
    Returns a report dictionary.
    """
    plan_path = Path("plan.md")
    spec_path = Path("specs/001-bird-migration-climate-correlation/spec.md")
    deviation_path = Path("data/provenance/spec_plan_deviation.json")
    output_path = Path("reports/plan_spec_alignment.json")

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 1. Verify files exist
    try:
        plan_text = load_file_text(plan_path)
        spec_text = load_file_text(spec_path)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Critical missing file for alignment check: {e}")

    # 2. Extract terms
    plan_terms = extract_terms(plan_text)
    spec_terms = extract_terms(spec_text)

    logger.info(f"Plan terms: {plan_terms}")
    logger.info(f"Spec terms: {spec_terms}")

    # 3. Load deviation whitelist
    whitelisted_deviations = set()
    if deviation_path.exists():
        try:
            with open(deviation_path, 'r', encoding='utf-8') as f:
                deviation_data = json.load(f)
                # Handle both single object and list of objects
                if isinstance(deviation_data, list):
                    for item in deviation_data:
                        if 'reason' in item:
                            whitelisted_deviations.add(item['reason'])
                elif isinstance(deviation_data, dict) and 'reason' in deviation_data:
                    whitelisted_deviations.add(deviation_data['reason'])
            logger.info(f"Loaded {len(whitelisted_deviations)} whitelisted deviations.")
        except json.JSONDecodeError:
            logger.warning("Failed to parse deviation whitelist JSON. Proceeding without whitelist.")

    # 4. Run checks
    contradictions = []
    
    # Check 1: Data Source Mismatch
    mismatch = check_data_source_mismatch(plan_terms, spec_terms)
    if mismatch:
        contradictions.append(mismatch)

    # Check 2: Year Range Mismatch
    year_mismatch = check_critical_data_scope_note(plan_terms, spec_terms)
    if year_mismatch:
        contradictions.append(year_mismatch)

    # Check 3: Unknown Terms
    unknown = check_unknown_terms(plan_terms, spec_terms)
    if unknown:
        contradictions.append(unknown)

    # 5. Filter contradictions against whitelist
    final_contradictions = []
    for c in contradictions:
        is_whitelisted = any(w.lower() in c.lower() for w in whitelisted_deviations)
        if not is_whitelisted:
            final_contradictions.append(c)
        else:
            logger.info(f"Whitelisted deviation found: {c}")

    # 6. Determine status
    status = "aligned" if not final_contradictions else "contradictions_found"
    
    report = {
        "status": status,
        "plan_file": str(plan_path),
        "spec_file": str(spec_path),
        "contradictions": final_contradictions,
        "whitelisted_count": len(whitelisted_deviations),
        "checked_at": str(Path().cwd()) # Placeholder for timestamp logic if needed
    }

    # 7. Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Alignment report written to {output_path}")

    if final_contradictions:
        raise RuntimeError(f"Plan/Spec alignment failed with unwhitelisted contradictions: {final_contradictions}")
    
    return report

def main():
    """Entry point for the script."""
    try:
        result = verify_alignment()
        print(json.dumps(result, indent=2))
        sys.exit(0)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except RuntimeError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
