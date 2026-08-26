"""
Extract study limitations from the project plan.md Assumptions section.

This script reads the `plan.md` file, locates the 'Assumptions' section,
and extracts specific limitations (e.g., CPU constraints, sample size).
It formats deferred empirical values with explicit placeholders as required.

Output: data/processed/limitation_text.md
"""
import os
import re
import logging
from pathlib import Path
from typing import List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root relative to this script (assuming code/report/structure)
# We need to find plan.md which is at the project root
def find_plan_md() -> Optional[Path]:
    """Locate plan.md starting from current directory up to root."""
    current = Path(__file__).resolve()
    # Traverse up to find plan.md
    for parent in [current] + list(current.parents):
        plan_path = parent / "plan.md"
        if plan_path.exists():
            return plan_path
    # Fallback: check standard locations relative to project root
    # Assuming script is in code/report/, project root is 2 levels up
    fallback = current.parent.parent / "plan.md"
    if fallback.exists():
        return fallback
    
    logger.error("Could not locate plan.md in parent directories.")
    return None

def extract_assumptions_section(plan_path: Path) -> Optional[str]:
    """
    Extract the content of the 'Assumptions' section from plan.md.
    
    Returns the raw text of the section or None if not found.
    """
    if not plan_path.exists():
        logger.error(f"Plan file not found: {plan_path}")
        return None

    try:
        with open(plan_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        logger.error(f"Failed to read plan.md: {e}")
        return None

    # Regex to find the Assumptions section
    # Matches "## Assumptions" or "# Assumptions" and captures until next header or EOF
    # We look for a section header that contains "Assumptions"
    pattern = r'#\s*Assumptions\s*\n(.*?)(?=\n#|$)'
    match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
    
    if match:
        section_content = match.group(1).strip()
        logger.info(f"Found Assumptions section with {len(section_content)} chars.")
        return section_content
    
    # Try alternative: maybe it's under a different parent header or just "Assumptions:"
    pattern_alt = r'Assumptions[:\s]*\n(.*?)(?=\n#|$)'
    match_alt = re.search(pattern_alt, content, re.DOTALL | re.IGNORECASE)
    if match_alt:
        return match_alt.group(1).strip()

    logger.warning("No 'Assumptions' section found in plan.md.")
    return None

def format_limitations_text(raw_text: str) -> str:
    """
    Format the extracted assumptions into a limitations markdown text.
    
    - Identifies specific constraints (CPU, sample size, etc.).
    - If empirical values are deferred (e.g., "sample size TBD"), formats them
      explicitly as 'Sample size: [deferred] - to be determined at runtime'.
    - Ensures the output is a valid Markdown string.
    """
    if not raw_text:
        return "# Study Limitations\n\nNo assumptions/limitations found in plan.md."

    lines = raw_text.split('\n')
    formatted_lines = ["# Study Limitations", ""]
    
    # Process lines to identify and format specific limitations
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Check for sample size mentions
        if re.search(r'sample\s*size', stripped, re.IGNORECASE):
            # Check if it's deferred or TBD
            if re.search(r'(tbd|deferred|runtime|to\s+determine|undetermined)', stripped, re.IGNORECASE):
                formatted_lines.append("- **Sample size**: [deferred] - to be determined at runtime")
            else:
                # Clean up the line for presentation
                clean_line = re.sub(r'\*+', '', stripped)
                formatted_lines.append(f"- {clean_line}")
        
        # Check for CPU/GPU constraints
        elif re.search(r'cpu|gpu|hardware|compute|resource', stripped, re.IGNORECASE):
            clean_line = re.sub(r'\*+', '', stripped)
            formatted_lines.append(f"- **Hardware/Compute**: {clean_line}")
        
        # Check for model constraints
        elif re.search(r'model|llm|inference', stripped, re.IGNORECASE):
            clean_line = re.sub(r'\*+', '', stripped)
            formatted_lines.append(f"- **Model Constraints**: {clean_line}")
        
        # General assumption
        else:
            # Remove markdown bullets if they exist to re-format consistently
            clean_line = re.sub(r'^[-*]\s*', '', stripped)
            if clean_line:
                formatted_lines.append(f"- {clean_line}")

    return "\n".join(formatted_lines)

def main():
    """Main entry point."""
    logger.info("Starting limitation extraction process.")
    
    # Locate plan.md
    plan_path = find_plan_md()
    if not plan_path:
        logger.error("Terminating: plan.md not found.")
        # We cannot proceed without the source of truth
        # Raise an error to fail loudly as per task constraints
        raise FileNotFoundError("Could not locate plan.md to extract limitations.")

    # Extract section
    raw_assumptions = extract_assumptions_section(plan_path)
    
    # Format text
    limitations_md = format_limitations_text(raw_assumptions or "")
    
    # Ensure output directory exists
    output_dir = Path(__file__).resolve().parent.parent / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / "limitation_text.md"
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(limitations_md)
        logger.info(f"Successfully wrote limitations to {output_path}")
    except Exception as e:
        logger.error(f"Failed to write output file: {e}")
        raise

if __name__ == "__main__":
    main()