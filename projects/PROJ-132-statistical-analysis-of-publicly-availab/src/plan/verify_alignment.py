import json
import logging
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configure logger for this module
logger = logging.getLogger(__name__)

def load_file_text(file_path: Path) -> str:
    """Load and return the text content of a file."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if file_path.stat().st_size == 0:
        raise FileNotFoundError(f"File is empty: {file_path}")
    return file_path.read_text(encoding="utf-8")

def extract_terms(text: str) -> List[str]:
    """Extract potential data source or requirement terms from text."""
    # Simple heuristic: look for capitalized phrases or specific keywords
    # that might indicate data sources or requirements.
    keywords = [
        "NOAA", "PRISM", "Daymet", "eBird", "vvud/eb-data",
        "migratory", "climate", "phenology", "temperature", "precipitation"
    ]
    found_terms = []
    for kw in keywords:
        if kw in text:
            found_terms.append(kw)
    return found_terms

def check_mandatory_a_priori_gp(spec_text: str, plan_text: str) -> List[str]:
    """Check for contradictions regarding mandatory GP random effects."""
    issues = []
    # Spec should require GP if it's a critical modeling requirement
    # Plan might omit or differ.
    # This is a placeholder logic for the specific task context.
    if "GP" in spec_text and "GP" not in plan_text:
        issues.append("Spec mentions GP random effect, Plan does not.")
    return issues

def check_critical_data_scope_note(spec_text: str, plan_text: str) -> List[str]:
    """Check for contradictions in critical data scope notes."""
    issues = []
    # Look for specific data source mentions
    if "Daymet" in spec_text and "NOAA" in plan_text:
        issues.append("Spec uses Daymet, Plan references NOAA.")
    if "vvud/eb-data" in spec_text and "full eBird" in plan_text:
        issues.append("Spec uses verified sample, Plan references full archive.")
    return issues

def check_data_source_mismatch(spec_text: str, plan_text: str) -> List[str]:
    """Detect specific data source mismatches between spec and plan."""
    issues = []
    # Define known pairs of conflicting sources
    conflicts = [
        ("NOAA/PRISM", "Daymet"),
        ("full eBird archive", "verified eBird sample"),
        ("vvud/eb-data", "full eBird")
    ]
    
    for spec_src, plan_src in conflicts:
        if spec_src in spec_text and plan_src in plan_text:
            issues.append(f"Data source mismatch: Spec requires '{spec_src}', Plan uses '{plan_src}'.")
    
    return issues

def check_unknown_terms(spec_text: str, plan_text: str) -> List[str]:
    """Check for terms in spec not found in plan (potential omissions)."""
    issues = []
    spec_terms = extract_terms(spec_text)
    plan_terms = extract_terms(plan_text)
    
    for term in spec_terms:
        if term not in plan_terms:
            issues.append(f"Term '{term}' found in Spec but not in Plan.")
    return issues

def load_deviation_whitelist(deviation_path: Path) -> List[Dict[str, Any]]:
    """Load the deviation whitelist JSON if it exists."""
    if not deviation_path.exists():
        return []
    try:
        content = deviation_path.read_text(encoding="utf-8")
        data = json.loads(content)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            # Handle single deviation object wrapped in a list or just return as list
            return [data]
        return []
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Could not load deviation whitelist: {e}")
        return []

def is_whitelisted(contradiction_msg: str, whitelist: List[Dict[str, Any]]) -> bool:
    """Check if a contradiction message is covered by the whitelist."""
    for entry in whitelist:
        spec_req = entry.get("spec_requirement", "")
        impl_src = entry.get("implemented_source", "")
        reason = entry.get("reason", "")
        
        # Check if the contradiction message contains key elements of the whitelist entry
        # A simple substring check is used here for robustness.
        # Ideally, we'd match specific IDs or structured fields.
        if spec_req and spec_req in contradiction_msg:
            return True
        if impl_src and impl_src in contradiction_msg:
            return True
        if reason and reason in contradiction_msg:
            return True
    return False

def verify_alignment(
    spec_path: Path,
    plan_path: Path,
    deviation_path: Path,
    output_path: Path
) -> bool:
    """
    Verify alignment between spec and plan, respecting the deviation whitelist.
    Returns True if alignment is valid (all contradictions are whitelisted), False otherwise.
    Raises RuntimeError if non-whitelisted contradictions exist.
    Raises FileNotFoundError if input files are missing.
    """
    logger.info(f"Verifying alignment: Spec={spec_path}, Plan={plan_path}")
    
    # 1. Verify files exist and are non-empty
    try:
        spec_text = load_file_text(spec_path)
        plan_text = load_file_text(plan_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        raise e

    # 2. Load deviation whitelist
    whitelist = load_deviation_whitelist(deviation_path)
    logger.info(f"Loaded {len(whitelist)} whitelisted deviations.")

    # 3. Check for contradictions
    all_issues = []
    all_issues.extend(check_data_source_mismatch(spec_text, plan_text))
    all_issues.extend(check_critical_data_scope_note(spec_text, plan_text))
    all_issues.extend(check_mandatory_a_priori_gp(spec_text, plan_text))
    all_issues.extend(check_unknown_terms(spec_text, plan_text))

    # 4. Filter issues against whitelist
    non_whitelisted_issues = []
    whitelisted_issues = []
    
    for issue in all_issues:
        if is_whitelisted(issue, whitelist):
            whitelisted_issues.append(issue)
            logger.info(f"Issue whitelisted: {issue}")
        else:
            non_whitelisted_issues.append(issue)
            logger.warning(f"Non-whitelisted contradiction found: {issue}")

    # 5. Generate output report
    report = {
        "spec_path": str(spec_path),
        "plan_path": str(plan_path),
        "deviation_whitelist_path": str(deviation_path),
        "whitelisted_count": len(whitelisted_issues),
        "non_whitelisted_count": len(non_whitelisted_issues),
        "whitelisted_issues": whitelisted_issues,
        "non_whitelisted_issues": non_whitelisted_issues,
        "status": "PASS" if len(non_whitelisted_issues) == 0 else "FAIL"
    }

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    logger.info(f"Alignment report written to {output_path}")

    if non_whitelisted_issues:
        error_msg = f"Non-whitelisted contradictions found: {non_whitelisted_issues}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    logger.info("Alignment verification passed.")
    return True

def main():
    """Main entry point for the verification script."""
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    spec_path = project_root / "specs" / "001-bird-migration-climate-correlation" / "spec.md"
    plan_path = project_root / "plan.md"
    deviation_path = project_root / "data" / "provenance" / "spec_plan_deviation.json"
    output_path = project_root / "reports" / "plan_spec_alignment.json"

    # Setup basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        verify_alignment(spec_path, plan_path, deviation_path, output_path)
        print(f"Success: Alignment verified. Report saved to {output_path}")
        sys.exit(0)
    except FileNotFoundError as e:
        print(f"Error: Missing required file. {e}")
        sys.exit(1)
    except RuntimeError as e:
        print(f"Error: Alignment failed due to contradictions. {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()