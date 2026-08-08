"""
Spec Amender Module for PROJ-527.

This module handles the correction of spec.md to align with the implementation plan,
specifically addressing FR-001, FR-005, FR-012, US-1, US-3, and the Assumptions section.
"""
import os
import sys
from pathlib import Path
from typing import List, Tuple

# Define the project root relative to this file
PROJECT_ROOT = Path(__file__).parent.parent

# Path to the spec file
SPEC_FILE_PATH = PROJECT_ROOT / "specs" / "001-prompt-complexity-evaluation" / "spec.md"

# The corrected FR-001 text
CORRECTED_FR001 = """FR-001: System MUST generate multiple prompt variants per HumanEval problem with controlled complexity levels defined by structural composition: simple (problem statement only), moderate (+1 example), complex (+constraints), very complex (+multi-step instructions), degenerate (+redundant constraints/examples). [UNRESOLVED-CLAIM: c_4fae1668 — status=not_enough_info] Token counts (using tiktoken cl100k_base, counting only prompt text) MUST serve as secondary indicators: simple ≤ 50 tokens, moderate 51-150 tokens, complex 151-300 tokens, very complex 301-500 tokens, degenerate > 500 tokens. [UNRESOLVED-CLAIM: c_77ebeea3 — status=not_enough_info] (See US-1)"""

# The corrected FR-005 text (replacing ANOVA/Kruskal-Wallis with LMM)
CORRECTED_FR005 = """FR-005: System MUST perform statistical analysis using Linear Mixed Models (LMM) to account for nested data structures (multiple variants per problem) with random intercepts for problem difficulty. ANOVA or Kruskal-Wallis tests are explicitly NOT permitted as the primary analysis method due to violation of independence assumptions."""

# The corrected FR-012 text (replacing code length with prompt token count)
CORRECTED_FR012 = """FR-012: System MUST use prompt token count as the primary covariate for readability metrics and statistical control, replacing the original 'code length (lines of code)' requirement. This aligns with the structural complexity definition in FR-001."""

# The corrected US-1 Acceptance Scenario 3
CORRECTED_US1_SCENARIO_3 = """3. **Manual Review Flagging**: The system MUST identify and flag samples where the 'degenerate' prompt token delta (vs 'very complex') is < 100 tokens. These samples MUST be written to `data/results/manual_review_queue.csv` with columns `problem_id`, `variant_label`, `token_delta`, `reason` for manual review. This ensures that structural complexity is not artificially inflated without corresponding token growth."""

# The corrected US-3 Acceptance Scenario 4
CORRECTED_US3_SCENARIO_4 = """4. **Structural Element Validation**: If the structural element count for 'degenerate' prompts is not strictly higher than 'very complex' prompts, the system MUST flag these instances for manual review. This validates the assumption that structural complexity correlates with prompt length and content density."""

# The corrected Assumptions Section
CORRECTED_ASSUMPTIONS = """## Assumptions

1. **HumanEval Availability**: The HumanEval dataset is available and accessible via the Hugging Face Hub (`openai/openai_humaneval`).
2. **CPU Constraints**: The LLM inference and code execution will run on CPU-only environments; therefore, timeouts and batch sizes are tuned for CPU performance.
3. **Tokenization Consistency**: The `tiktoken cl100k_base` tokenizer accurately reflects the tokenization behavior of the target LLM for the purpose of complexity estimation.
4. **Statistical Power**: The sample size of HumanEval (164 problems) is sufficient to detect medium-to-large effect sizes in pass rates across complexity levels, though power may be limited for small effects.
5. **Code Execution Safety**: Generated code is executed in a sandboxed environment to prevent security vulnerabilities."""

def apply_patch() -> bool:
    """
    Applies the required patches to spec.md.

    Returns:
        bool: True if successful, False otherwise.
    """
    if not SPEC_FILE_PATH.exists():
        print(f"ERROR: Spec file not found at {SPEC_FILE_PATH}")
        return False

    try:
        content = SPEC_FILE_PATH.read_text(encoding='utf-8')
        
        # 1. Replace FR-001
        # We look for the start of FR-001 and replace until the next FR-XX or end of section
        import re
        
        # Pattern to match FR-001 block
        pattern_fr001 = r'FR-001:.*?(?=\nFR-00[2-9]|\n##|\Z)'
        if re.search(pattern_fr001, content, re.DOTALL):
            content = re.sub(pattern_fr001, CORRECTED_FR001, content, flags=re.DOTALL)
        else:
            # Fallback: try to find "FR-001" and replace the line/paragraph
            if "FR-001:" in content:
                # Simple line replacement if regex fails
                lines = content.split('\n')
                new_lines = []
                skip = False
                for line in lines:
                    if line.startswith('FR-001:'):
                        new_lines.append(CORRECTED_FR001)
                        skip = True
                    elif skip and (line.startswith('FR-00') or line.startswith('##')):
                        skip = False
                        new_lines.append(line)
                    elif not skip:
                        new_lines.append(line)
                content = '\n'.join(new_lines)

        # 2. Replace FR-005
        pattern_fr005 = r'FR-005:.*?(?=\nFR-00[6-9]|\n##|\Z)'
        if re.search(pattern_fr005, content, re.DOTALL):
            content = re.sub(pattern_fr005, CORRECTED_FR005, content, flags=re.DOTALL)
        else:
            if "FR-005:" in content:
                lines = content.split('\n')
                new_lines = []
                skip = False
                for line in lines:
                    if line.startswith('FR-005:'):
                        new_lines.append(CORRECTED_FR005)
                        skip = True
                    elif skip and (line.startswith('FR-00') or line.startswith('##')):
                        skip = False
                        new_lines.append(line)
                    elif not skip:
                        new_lines.append(line)
                content = '\n'.join(new_lines)

        # 3. Replace FR-012
        pattern_fr012 = r'FR-012:.*?(?=\nFR-01[3-9]|\n##|\Z)'
        if re.search(pattern_fr012, content, re.DOTALL):
            content = re.sub(pattern_fr012, CORRECTED_FR012, content, flags=re.DOTALL)
        else:
            if "FR-012:" in content:
                lines = content.split('\n')
                new_lines = []
                skip = False
                for line in lines:
                    if line.startswith('FR-012:'):
                        new_lines.append(CORRECTED_FR012)
                        skip = True
                    elif skip and (line.startswith('FR-01') or line.startswith('##')):
                        skip = False
                        new_lines.append(line)
                    elif not skip:
                        new_lines.append(line)
                content = '\n'.join(new_lines)

        # 4. Update US-1 Acceptance Scenario 3
        # Look for the specific scenario text and replace it
        old_scenario_3 = "3. **Manual Review Flagging**: The system MUST identify and flag samples where the 'degenerate' prompt token delta (vs 'very complex') is < 100 tokens."
        if old_scenario_3 in content:
            content = content.replace(old_scenario_3, CORRECTED_US1_SCENARIO_3.split('\n')[0]) # Replace just the line if it's short, or handle block
            # Better: Replace the whole block if we can identify it
            # For safety, we do a simple string replacement for the key phrase
            content = content.replace(
                "3. **Manual Review Flagging**: The system MUST identify and flag samples where the 'degenerate' prompt token delta (vs 'very complex') is < 100 tokens.",
                "3. **Manual Review Flagging**: The system MUST identify and flag samples where the 'degenerate' prompt token delta (vs 'very complex') is < 100 tokens. These samples MUST be written to `data/results/manual_review_queue.csv` with columns `problem_id`, `variant_label`, `token_delta`, `reason` for manual review. This ensures that structural complexity is not artificially inflated without corresponding token growth."
            )

        # 5. Update US-3 Acceptance Scenario 4
        content = content.replace(
            "4. **Structural Element Validation**: If the structural element count for 'degenerate' prompts is not strictly higher than 'very complex' prompts, the system MUST flag these instances for manual review.",
            CORRECTED_US3_SCENARIO_4
        )

        # 6. Replace Assumptions Section
        # Find the Assumptions header and replace the content until the next header
        pattern_assumptions = r'## Assumptions.*?(?=\n##|\Z)'
        if re.search(pattern_assumptions, content, re.DOTALL):
            content = re.sub(pattern_assumptions, "## Assumptions\n\n" + "\n\n".join(CORRECTED_ASSUMPTIONS.split('\n')[1:]), content, flags=re.DOTALL)
        else:
            # If not found, append to end or create section
            if "## Assumptions" not in content:
                content += "\n\n## Assumptions\n\n" + "\n\n".join(CORRECTED_ASSUMPTIONS.split('\n')[1:])

        # Write back
        SPEC_FILE_PATH.write_text(content, encoding='utf-8')
        print(f"Successfully updated {SPEC_FILE_PATH}")
        return True

    except Exception as e:
        print(f"ERROR: Failed to update spec.md: {e}")
        return False

def verify_amendments() -> Tuple[bool, List[str]]:
    """
    Verifies that the amendments have been applied correctly.

    Returns:
        Tuple[bool, List[str]]: (Success, List of missing/incorrect items)
    """
    if not SPEC_FILE_PATH.exists():
        return False, ["spec.md not found"]

    content = SPEC_FILE_PATH.read_text(encoding='utf-8')
    errors = []

    # Check FR-001
    if "Linear Mixed Models (LMM)" not in CORRECTED_FR001:
        # We are checking if the text contains the key corrected phrases
        pass
    
    checks = [
        (CORRECTED_FR001, "FR-001"),
        ("Linear Mixed Models (LMM)", "FR-005"),
        ("prompt token count", "FR-012"),
        ("manual_review_queue.csv", "US-1 Scenario 3"),
        ("Structural Element Validation", "US-3 Scenario 4"),
        ("HumanEval dataset is available", "Assumptions")
    ]

    for text, label in checks:
        if text not in content:
            errors.append(f"Missing or incorrect: {label}")

    return len(errors) == 0, errors

def main():
    """Main entry point for the spec amender."""
    print("Applying Spec Amendments for PROJ-527...")
    success = apply_patch()
    if success:
        is_valid, errors = verify_amendments()
        if is_valid:
            print("Verification PASSED. All amendments applied correctly.")
            sys.exit(0)
        else:
            print("Verification FAILED. Errors found:")
            for err in errors:
                print(f"  - {err}")
            sys.exit(1)
    else:
        print("Failed to apply amendments.")
        sys.exit(1)

if __name__ == "__main__":
    main()
