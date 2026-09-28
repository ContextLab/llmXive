import os
import sys
import logging
from pathlib import Path
import json

# Add project root to path to allow imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def find_section_5(file_path: Path) -> str:
    """
    Locate Section 5 'Methodological Notes' in the spec file.
    Returns the text content of Section 5 or empty string if not found.
    """
    if not file_path.exists():
        logging.error(f"Spec file not found: {file_path}")
        return ""

    content = file_path.read_text(encoding='utf-8')
    lines = content.split('\n')
    
    section_5_start = -1
    section_6_start = -1
    
    # Look for Section 5 header
    for i, line in enumerate(lines):
        if line.strip().startswith('## ') and 'Methodological Notes' in line:
            section_5_start = i
            # Find the next section (##) to mark end of Section 5
            for j in range(i + 1, len(lines)):
                if lines[j].strip().startswith('## '):
                    section_6_start = j
                    break
            break
    
    if section_5_start == -1:
        logging.error("Section 5 'Methodological Notes' not found in spec.")
        return ""
    
    if section_6_start == -1:
        # Section 5 extends to end of file
        return '\n'.join(lines[section_5_start:])
    else:
        return '\n'.join(lines[section_5_start:section_6_start])

def verify_alignment(section_text: str) -> dict:
    """
    Verify that Section 5 contains the 'Revised Approach' rationale
    and handles 'Synthetic Cohort' correctly (only in rejection context).
    
    Returns a dict with verification status and details.
    """
    result = {
        'verified': True,
        'has_revised_approach': False,
        'synthetic_cohort_in_rejection_only': False,
        'issues': []
    }
    
    if not section_text:
        result['verified'] = False
        result['issues'].append("Section 5 text is empty")
        return result
    
    # Check for "Revised Approach" text
    revised_keywords = ["Revised Approach", "Single-Dataset", "single-dataset", "revised approach"]
    found_revised = any(keyword.lower() in section_text.lower() for keyword in revised_keywords)
    
    if found_revised:
        result['has_revised_approach'] = True
        logging.info("Found 'Revised Approach' rationale in Section 5.")
    else:
        result['verified'] = False
        result['issues'].append("Missing 'Revised Approach' rationale")
        logging.error("Missing 'Revised Approach' rationale in Section 5.")
    
    # Check "Synthetic Cohort" occurrences
    synthetic_cohort_count = section_text.lower().count("synthetic cohort")
    
    if synthetic_cohort_count == 0:
        # If not mentioned at all, that's acceptable if it's not needed
        result['synthetic_cohort_in_rejection_only'] = True
        logging.info("'Synthetic Cohort' not mentioned in Section 5 (acceptable if not relevant).")
    else:
        # Must appear ONLY in rejection context
        rejection_keywords = ["rejected", "rejection", "invalid", "excluded", "removed", "deprecated", "methodologically invalid"]
        
        # Check if every occurrence is near a rejection keyword
        lines = section_text.split('\n')
        all_in_rejection = True
        
        for line in lines:
            if "synthetic cohort" in line.lower():
                # Check if this line or nearby lines contain rejection context
                line_lower = line.lower()
                has_rejection_context = any(kw in line_lower for kw in rejection_keywords)
                
                if not has_rejection_context:
                    # Check surrounding context (previous and next 2 lines)
                    line_idx = lines.index(line)
                    context_start = max(0, line_idx - 2)
                    context_end = min(len(lines), line_idx + 3)
                    context = ' '.join(lines[context_start:context_end]).lower()
                    
                    if not any(kw in context for kw in rejection_keywords):
                        all_in_rejection = False
                        result['issues'].append(f"'Synthetic Cohort' found outside rejection context: '{line.strip()}'")
        
        if all_in_rejection:
            result['synthetic_cohort_in_rejection_only'] = True
            logging.info("All mentions of 'Synthetic Cohort' are in rejection context.")
        else:
            result['verified'] = False
            logging.error("Found 'Synthetic Cohort' outside of rejection context.")
    
    return result

def main():
    """
    Main entry point for verifying methodological notes alignment.
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('data/results/methodology_verification.log')
        ]
    )
    
    # Define paths
    spec_path = Path("specs/001-social-support-resilience/spec.md")
    output_path = Path("data/results/methodology_verification.json")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logging.info(f"Verifying methodological notes in: {spec_path}")
    
    # Find Section 5
    section_text = find_section_5(spec_path)
    
    if not section_text:
        logging.error("Failed to extract Section 5. Aborting verification.")
        # Write failure result
        result = {
            'verified': False,
            'error': 'Section 5 not found',
            'issues': ['Section 5 not found in spec']
        }
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        sys.exit(1)
    
    # Verify alignment
    verification_result = verify_alignment(section_text)
    
    # Log final status
    if verification_result['verified']:
        logging.info("INFO: Methodological Notes verified.")
    else:
        logging.error("ERROR: Methodological Notes mismatch.")
        for issue in verification_result['issues']:
            logging.error(f"  - {issue}")
    
    # Write result to file
    with open(output_path, 'w') as f:
        json.dump(verification_result, f, indent=2)
    
    logging.info(f"Verification result written to: {output_path}")
    
    # Exit with appropriate code
    sys.exit(0 if verification_result['verified'] else 1)

if __name__ == "__main__":
    main()