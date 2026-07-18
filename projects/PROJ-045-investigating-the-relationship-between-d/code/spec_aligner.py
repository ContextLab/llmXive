"""
Task T002: Spec Alignment Verification
Confirms that spec.md Section 3.2 and FR-003 explicitly mandate
"2x2x2 minimum supercell expansion" and supersede the previous ≤8 atom constraint.
"""
import logging
import os
from pathlib import Path
from typing import List, Tuple

# Import existing logging utility
from utils import setup_logging

def load_spec_text(spec_path: Path) -> str:
    """Read the full content of spec.md."""
    if not spec_path.exists():
        raise FileNotFoundError(f"Spec file not found at {spec_path}")
    return spec_path.read_text(encoding="utf-8")

def verify_section_3_2(content: str) -> Tuple[bool, List[str]]:
    """
    Check if Section 3.2 mentions '2x2x2' or 'supercell expansion' mandates.
    Returns (is_valid, list_of_findings).
    """
    findings = []
    is_valid = False
    
    # Normalize content for search
    lines = content.split('\n')
    in_section_3_2 = False
    section_content = []

    for line in lines:
        if 'Section 3.2' in line or '3.2' in line and 'Methodology' in line:
            in_section_3_2 = True
        if in_section_3_2:
            section_content.append(line)
            # Heuristic for end of section (next section header)
            if line.strip().startswith('3.3') or line.strip().startswith('3.4'):
                break

    section_text = '\n'.join(section_content)
    
    checks = [
        "2x2x2",
        "supercell",
        "expansion",
        "minimum",
        "constraint"
    ]
    
    found_terms = [term for term in checks if term in section_text.lower()]
    
    if "2x2x2" in section_text.lower() and "supercell" in section_text.lower():
        is_valid = True
        findings.append("CONFIRMED: Section 3.2 explicitly mentions '2x2x2 supercell'.")
    elif "supercell" in section_text.lower():
        findings.append("WARNING: 'supercell' found in 3.2, but '2x2x2' not explicitly detected.")
    else:
        findings.append("ERROR: No mention of supercell expansion in Section 3.2.")

    return is_valid, findings

def verify_fr_003(content: str) -> Tuple[bool, List[str]]:
    """
    Check if FR-003 explicitly mandates the 2x2x2 expansion and supersedes ≤8 atom constraint.
    """
    findings = []
    is_valid = False

    # Search for FR-003 block
    lines = content.split('\n')
    in_fr_003 = False
    fr_content = []

    for line in lines:
        if 'FR-003' in line or 'FR003' in line:
            in_fr_003 = True
        if in_fr_003:
            fr_content.append(line)
            # End of requirement usually marked by next FR or section
            if line.strip().startswith('FR-00') or line.strip().startswith('##'):
                if 'FR-003' not in line:
                    break

    fr_text = '\n'.join(fr_content)
    
    # Check for specific keywords indicating superseding
    required_terms = ["2x2x2", "supersede", "constraint", "8 atom"]
    found_terms = [term for term in required_terms if term in fr_text.lower()]
    
    if "2x2x2" in fr_text.lower() and ("supersede" in fr_text.lower() or "override" in fr_text.lower()):
        is_valid = True
        findings.append("CONFIRMED: FR-003 explicitly mandates 2x2x2 and supersedes previous constraints.")
    elif "2x2x2" in fr_text.lower():
        findings.append("PARTIAL: FR-003 mentions 2x2x2, but explicit superseding language not detected.")
    else:
        findings.append("ERROR: FR-003 does not appear to mandate 2x2x2 expansion.")

    return is_valid, findings

def generate_alignment_log(
    spec_content: str,
    section_valid: bool,
    section_findings: List[str],
    fr_valid: bool,
    fr_findings: List[str],
    output_path: Path
) -> None:
    """Write the verification results to the log file."""
    log_lines = [
        "SPECIFICATION ALIGNMENT LOG",
        "Task: T002 - Confirm 2x2x2 Supercell Mandate",
        "Date: " + __import__('datetime').datetime.now().isoformat(),
        "=" * 60,
        "",
        "VERIFICATION TARGET:",
        "  - Spec Section: 3.2",
        "  - Functional Requirement: FR-003",
        "  - Mandate: 2x2x2 minimum supercell expansion superseding ≤8 atom constraint",
        "",
        "SECTION 3.2 ANALYSIS:",
    ]
    log_lines.extend([f"  {f}" for f in section_findings])
    log_lines.append("")
    log_lines.append("FR-003 ANALYSIS:")
    log_lines.extend([f"  {f}" for f in fr_findings])
    log_lines.append("")
    
    overall_status = "PASS" if (section_valid and fr_valid) else "REVIEW_REQUIRED"
    if not section_valid and not fr_valid:
        overall_status = "FAIL"

    log_lines.append("OVERALL STATUS:")
    log_lines.append(f"  {overall_status}")
    log_lines.append("")
    log_lines.append("CONCLUSION:")
    if overall_status == "PASS":
        log_lines.append("  The specification explicitly authorizes the 2x2x2 supercell expansion.")
        log_lines.append("  Implementation in T024 and T031 is authorized per this alignment.")
    else:
        log_lines.append("  The specification does not clearly authorize the 2x2x2 expansion.")
        log_lines.append("  Implementation of T024 and T031 is BLOCKED pending spec revision.")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text('\n'.join(log_lines) + '\n', encoding='utf-8')
    logging.info(f"Alignment log written to {output_path}")

def main():
    """Entry point for T002."""
    logger = setup_logging("spec_aligner")
    
    # Determine paths
    project_root = Path(__file__).resolve().parent.parent
    spec_path = project_root / "specs" / "001-defect-chemistry-conductivity" / "spec.md"
    output_path = project_root / "data" / "processed" / "spec_alignment_log.txt"

    logger.info(f"Loading spec from {spec_path}")
    
    try:
        spec_content = load_spec_text(spec_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        # Create a log indicating failure to find spec
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(f"ERROR: Spec file not found at {spec_path}. Cannot verify alignment.\n", encoding='utf-8')
        return

    logger.info("Verifying Section 3.2...")
    section_valid, section_findings = verify_section_3_2(spec_content)
    
    logger.info("Verifying FR-003...")
    fr_valid, fr_findings = verify_fr_003(spec_content)

    generate_alignment_log(
        spec_content,
        section_valid,
        section_findings,
        fr_valid,
        fr_findings,
        output_path
    )

    logger.info("Task T002 completed.")

if __name__ == "__main__":
    main()
