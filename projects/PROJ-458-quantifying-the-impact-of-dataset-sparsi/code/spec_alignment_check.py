"""
Task T055: Document that `spec.md` FR-006 specifies "Linear Mixed-Effects Modeling (LMM)".
This script verifies the alignment between the Plan's deviation (LMM) and the Spec's FR-006.
It logs "PASS" if the specification explicitly mentions LMM, otherwise it fails loudly.
"""
import os
import sys
import json
from pathlib import Path
from utils.logging import get_logger

def load_spec_content(spec_path: Path) -> str:
    """Load the content of spec.md."""
    if not spec_path.exists():
        raise FileNotFoundError(f"Specification file not found at {spec_path}")
    with open(spec_path, "r", encoding="utf-8") as f:
        return f.read()

def check_fr006_alignment(content: str) -> bool:
    """
    Check if FR-006 in the spec explicitly mentions 'Linear Mixed-Effects Modeling' or 'LMM'.
    The Plan deviated from ANOVA to LMM; the Spec must reflect this.
    """
    # Look for the specific requirement text
    indicators = [
        "FR-006",
        "Linear Mixed-Effects Modeling",
        "Linear Mixed-Effects",
        "LMM",
        "MixedLM"
    ]
    
    # Simple heuristic: Check if FR-006 section exists and contains LMM keywords
    # We assume the spec has a structure where FR-006 is a distinct block
    lines = content.split('\n')
    in_fr006 = False
    fr006_content = []
    
    for line in lines:
        if "FR-006" in line:
            in_fr006 = True
        if in_fr006:
            fr006_content.append(line)
            # Stop at the next FR-XX or end of file logic (simplified)
            if line.strip().startswith("FR-0") and "FR-006" not in line:
                break
    
    fr006_text = "\n".join(fr006_content).lower()
    
    # Check for LMM indicators
    has_lmm = any(term.lower() in fr006_text for term in ["linear mixed-effects", "lmm", "mixedlm"])
    has_anova = "anova" in fr006_text and "mixed" not in fr006_text
    
    if not has_lmm:
        logger = get_logger()
        logger.warning("FR-006 does not explicitly mention Linear Mixed-Effects Modeling (LMM).")
        logger.warning("Current content snippet: " + fr006_text[:200])
        return False
    
    if has_anova and not has_lmm:
        logger = get_logger()
        logger.warning("FR-006 mentions ANOVA but not LMM. Plan deviation not reflected.")
        return False
        
    return True

def main():
    logger = get_logger()
    logger.info("Starting T055: Verifying FR-006 alignment for Linear Mixed-Effects Modeling.")
    
    # Determine spec path relative to project root
    # Assuming code/ is the root for this script, spec is in specs/ or root
    possible_paths = [
        Path("specs/001-quantifying-the-impact-of-dataset-sparsity/spec.md"),
        Path("spec.md"),
        Path("../spec.md"),
        Path("../../spec.md")
    ]
    
    spec_path = None
    for p in possible_paths:
        if p.exists():
            spec_path = p
            break
    
    if not spec_path:
        logger.error("Could not locate spec.md file.")
        print("FAIL: spec.md not found")
        sys.exit(1)
    
    try:
        content = load_spec_content(spec_path)
        is_aligned = check_fr006_alignment(content)
        
        if is_aligned:
            logger.info("PASS: FR-006 correctly specifies Linear Mixed-Effects Modeling (LMM).")
            print("PASS")
            
            # Log the alignment record
            alignment_record = {
                "task_id": "T055",
                "status": "PASS",
                "check": "FR-006 LMM Alignment",
                "spec_path": str(spec_path),
                "timestamp": str(Path.cwd()) # Simplified timestamp logic
            }
            
            # Ensure results directory exists
            results_dir = Path("data/results")
            results_dir.mkdir(parents=True, exist_ok=True)
            
            log_path = results_dir / "spec_alignment_t055.json"
            with open(log_path, "w", encoding="utf-8") as f:
                json.dump(alignment_record, f, indent=2)
            
            logger.info(f"Alignment record saved to {log_path}")
        else:
            logger.error("FAIL: FR-006 does not specify LMM. Spec deviation not resolved.")
            print("FAIL: FR-006 does not specify LMM")
            sys.exit(1)
            
    except FileNotFoundError as e:
        logger.error(f"File error: {e}")
        print(f"FAIL: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"FAIL: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
