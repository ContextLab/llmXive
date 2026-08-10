import os
import sys
from pathlib import Path
import logging
from logging_config import get_logger

logger = get_logger(__name__)

def load_file_text(filepath: str) -> str:
    """Load text content from a file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"File not found: {filepath}")
        raise
    except Exception as e:
        logger.error(f"Error reading {filepath}: {e}")
        raise

def check_spec_alignment(spec_content: str, plan_content: str) -> dict:
    """
    Verify alignment between spec.md and plan.md regarding the statistical method.
    
    Returns a dictionary with verification results and any flags.
    """
    results = {
        "spec_valid": False,
        "plan_valid": False,
        "aligned": False,
        "flags": [],
        "details": {}
    }

    # Check Spec Content
    spec_has_max_stat = "Maximum Statistic" in spec_content or "Maximum Statistic approach" in spec_content
    spec_no_bh = "Benjamini-Hochberg correction is NOT used" in spec_content or "BH is NOT used" in spec_content
    
    # Check for contradictory BH mandate in spec (should not exist)
    spec_mandates_bh = "Spec mandates BH" in spec_content or ("Benjamini-Hochberg" in spec_content and "must be used" in spec_content)

    if spec_has_max_stat and spec_no_bh and not spec_mandates_bh:
        results["spec_valid"] = True
        results["details"]["spec"] = "Spec correctly states Maximum Statistic and forbids BH."
    else:
        if not spec_has_max_stat:
            results["flags"].append("Spec missing 'Maximum Statistic' statement.")
        if not spec_no_bh:
            results["flags"].append("Spec missing 'BH is NOT used' statement.")
        if spec_mandates_bh:
            results["flags"].append("CRITICAL: Spec incorrectly mandates BH.")
        results["details"]["spec"] = "Spec validation failed."

    # Check Plan Content
    plan_has_max_stat = "Maximum Statistic" in plan_content
    plan_no_bh = "Benjamini-Hochberg" not in plan_content or ("Benjamini-Hochberg" in plan_content and "NOT" in plan_content)
    
    # Check for the specific documentation error in the Plan
    plan_has_error_note = "Note on Spec Conflict" in plan_content
    plan_claims_spec_mandates_bh = "Spec mandates BH" in plan_content

    if plan_has_max_stat:
        results["plan_valid"] = True
        results["details"]["plan"] = "Plan correctly implements Maximum Statistic."
    else:
        results["flags"].append("Plan missing 'Maximum Statistic' implementation statement.")
        results["details"]["plan"] = "Plan validation failed."

    # Check for the specific documentation error
    if plan_has_error_note and plan_claims_spec_mandates_bh:
        results["flags"].append("DOCUMENTATION ERROR: Plan's 'Note on Spec Conflict' incorrectly claims Spec mandates BH.")
    
    # Determine Alignment
    if results["spec_valid"] and results["plan_valid"]:
        # If both are valid, they are aligned on the method (Max Stat)
        # The documentation error in the plan is a flag, but doesn't break method alignment
        results["aligned"] = True
        if results["flags"]:
            results["details"]["alignment"] = "Aligned on method, but documentation errors detected."
        else:
            results["details"]["alignment"] = "Fully aligned."
    else:
        results["aligned"] = False
        results["details"]["alignment"] = "Not aligned due to validation failures."

    return results

def main():
    """
    Main entry point for T001: Spec Alignment Verification.
    
    Reads spec.md and plan.md, verifies consistency on statistical method,
    and writes the alignment log to data/reports/spec_alignment_log.txt.
    """
    # Determine base path (project root)
    # Assuming script runs from project root or code/
    base_path = Path.cwd()
    if (base_path / "code").exists():
        base_path = base_path.parent if base_path.name == "code" else base_path
    
    spec_path = base_path / "specs" / "001-assessing-the-validity-of-the-cosmologic" / "spec.md"
    plan_path = base_path / "specs" / "001-assessing-the-validity-of-the-cosmologic" / "plan.md"
    output_dir = base_path / "data" / "reports"
    output_file = output_dir / "spec_alignment_log.txt"

    logger.info(f"Starting Spec Alignment Check (T001)")
    logger.info(f"Spec Path: {spec_path}")
    logger.info(f"Plan Path: {plan_path}")
    logger.info(f"Output Path: {output_file}")

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Load files
        if not spec_path.exists():
            raise FileNotFoundError(f"Spec file not found: {spec_path}")
        if not plan_path.exists():
            raise FileNotFoundError(f"Plan file not found: {plan_path}")

        spec_content = load_file_text(str(spec_path))
        plan_content = load_file_text(str(plan_path))

        # Perform check
        results = check_spec_alignment(spec_content, plan_content)

        # Generate Log Content
        log_lines = []
        log_lines.append("=" * 60)
        log_lines.append("SPEC ALIGNMENT VERIFICATION LOG (T001)")
        log_lines.append("=" * 60)
        log_lines.append(f"Date: {Path.cwd().name}") # Placeholder for actual date
        log_lines.append("")
        log_lines.append("VERIFICATION RESULTS:")
        log_lines.append(f"  Spec Valid: {results['spec_valid']}")
        log_lines.append(f"  Plan Valid: {results['plan_valid']}")
        log_lines.append(f"  Aligned: {results['aligned']}")
        log_lines.append("")
        
        if results['details']:
            log_lines.append("DETAILS:")
            for key, value in results['details'].items():
                log_lines.append(f"  {key}: {value}")
            log_lines.append("")

        if results['flags']:
            log_lines.append("FLAGS / WARNINGS:")
            for flag in results['flags']:
                log_lines.append(f"  - {flag}")
            log_lines.append("")

        if results['aligned']:
            log_lines.append("CONCLUSION:")
            log_lines.append("  Spec Alignment Verified: Spec and Plan both mandate Maximum Statistic.")
            if any("DOCUMENTATION ERROR" in f for f in results['flags']):
                log_lines.append("  Plan's 'Note on Spec Conflict' is flagged as a documentation error (incorrectly claims Spec mandates BH).")
            log_lines.append("  Implementation tasks may proceed.")
            status = "SUCCESS"
        else:
            log_lines.append("CONCLUSION:")
            log_lines.append("  HALT: Spec/Plan Mismatch detected. Implementation cannot proceed.")
            status = "FAILURE"

        log_lines.append("")
        log_lines.append(f"STATUS: {status}")
        log_lines.append("=" * 60)

        # Write output
        log_text = "\n".join(log_lines)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(log_text)

        logger.info(f"Alignment log written to {output_file}")
        logger.info(f"Status: {status}")

        if not results['aligned']:
            sys.exit(1)

    except FileNotFoundError as e:
        logger.error(f"Missing required file: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during alignment check: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
