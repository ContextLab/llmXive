"""
Task T011c: Update research.md with MDE estimation results.

Reads data/processed/pilot_mde_results.json and appends a section
'MDE_Estimation' to research.md.
"""
import json
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Add project root to path for imports if needed, though this script is self-contained
project_root = Path(__file__).resolve().parent.parent
research_md_path = project_root / "research.md"
pilot_results_path = project_root / "data" / "processed" / "pilot_mde_results.json"

def load_pilot_results(path: Path) -> Optional[Dict[str, Any]]:
    """Load the pilot MDE results JSON file."""
    if not path.exists():
        raise FileNotFoundError(f"Pilot results file not found: {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def format_mde_section(results: Dict[str, Any]) -> str:
    """Format the MDE estimation section content."""
    lines = [
        "",
        "## MDE_Estimation",
        "",
        "Minimum Detectable Effect (MDE) estimation based on pilot analysis:",
        ""
    ]
    
    # Extract and format key metrics
    mde = results.get('minimum_detectable_effect')
    power = results.get('power')
    sample_size = results.get('sample_size')
    
    if mde is not None:
        lines.append(f"- **Minimum Detectable Effect (MDE)**: {mde:.4f}")
    if power is not None:
        lines.append(f"- **Statistical Power**: {power:.2%}")
    if sample_size is not None:
        lines.append(f"- **Required Sample Size**: {sample_size:,} dialogues")
    
    # Include any additional context from the results
    if 'notes' in results and results['notes']:
        lines.append("")
        lines.append("**Notes:**")
        lines.append(f"- {results['notes']}")
    
    lines.append("")
    return "\n".join(lines)

def update_research_md(research_path: Path, mde_content: str) -> None:
    """Append MDE section to research.md."""
    if not research_path.exists():
        # Create the file if it doesn't exist
        with open(research_path, 'w', encoding='utf-8') as f:
            f.write("# Research Plan\n")
            f.write("\n")
            f.write("This document outlines the research methodology and findings.\n")
            f.write("\n")
    
    # Read existing content
    with open(research_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if MDE section already exists to avoid duplication
    if "## MDE_Estimation" in content:
        # Find the section and replace it
        lines = content.split('\n')
        new_lines = []
        skip_until_next_header = False
        
        for i, line in enumerate(lines):
            if line.strip() == "## MDE_Estimation":
                skip_until_next_header = True
                new_lines.append(line)
                new_lines.append(mde_content)
                continue
            
            if skip_until_next_header:
                # Check if we've reached the next section header
                if line.startswith("## ") and line != "## MDE_Estimation":
                    skip_until_next_header = False
                    new_lines.append(line)
                # Otherwise skip this line (it's part of the old MDE section)
                continue
            
            new_lines.append(line)
        
        updated_content = '\n'.join(new_lines)
    else:
        # Append to the end
        updated_content = content.rstrip() + mde_content
    
    # Write back
    with open(research_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)

def main() -> int:
    """Main entry point for the script."""
    try:
        # Load pilot results
        results = load_pilot_results(pilot_results_path)
        
        # Format the section
        mde_section = format_mde_section(results)
        
        # Update research.md
        update_research_md(research_md_path, mde_section)
        
        print(f"Successfully updated {research_md_path} with MDE estimation results.")
        return 0
    
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in pilot results file: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())