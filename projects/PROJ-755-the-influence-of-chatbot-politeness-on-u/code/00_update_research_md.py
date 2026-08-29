import json
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any

def load_pilot_results(path: str) -> Dict[str, Any]:
    """Load the pilot MDE results JSON file."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Pilot results file not found: {path}")
    with open(p, 'r', encoding='utf-8') as f:
        return json.load(f)

def format_mde_section(data: Dict[str, Any]) -> str:
    """Format the MDE estimation results as a Markdown section."""
    lines = [
        "## MDE_Estimation",
        "",
        f"- **Minimum Detectable Effect (MDE)**: {data.get('minimum_detectable_effect', 'N/A')}",
        f"- **Statistical Power**: {data.get('power', 'N/A')}",
        f"- **Sample Size Used**: {data.get('sample_size', 'N/A')}",
        "",
        "### Details",
        "",
    ]
    
    # Add any additional context if present
    if 'effect_size' in data:
        lines.append(f"- **Estimated Effect Size**: {data['effect_size']}")
    if 'alpha' in data:
        lines.append(f"- **Significance Level (alpha)**: {data['alpha']}")
    if 'two_tailed' in data:
        lines.append(f"- **Test Type**: {'Two-tailed' if data['two_tailed'] else 'One-tailed'}")
    
    lines.append("---")
    return "\n".join(lines)

def update_research_md(mde_results_path: str, research_md_path: Optional[str] = None) -> str:
    """
    Update research.md with the MDE estimation results.
    
    Args:
        mde_results_path: Path to the pilot_mde_results.json file.
        research_md_path: Path to research.md. If None, defaults to 'docs/research.md'.
        
    Returns:
        Path to the updated research.md file.
    """
    if research_md_path is None:
        research_md_path = "docs/research.md"
    
    # Load pilot results
    results = load_pilot_results(mde_results_path)
    
    # Format the section
    mde_section = format_mde_section(results)
    
    # Read existing research.md if it exists
    research_file = Path(research_md_path)
    existing_content = ""
    if research_file.exists():
        with open(research_file, 'r', encoding='utf-8') as f:
            existing_content = f.read()
    
    # Check if MDE_Estimation section already exists
    if "## MDE_Estimation" in existing_content:
        # Replace existing section
        lines = existing_content.split('\n')
        new_lines = []
        skip = False
        for i, line in enumerate(lines):
            if line.strip() == "## MDE_Estimation":
                # Start of section to replace
                skip = True
                new_lines.append(mde_section)
                # Skip until next section or end
                while i + 1 < len(lines):
                    i += 1
                    if lines[i].startswith('## '):
                        new_lines.append(lines[i])
                        skip = False
                        break
            elif skip:
                continue
            else:
                new_lines.append(line)
        
        updated_content = "\n".join(new_lines)
    else:
        # Append new section
        if existing_content and not existing_content.endswith('\n'):
            existing_content += "\n"
        updated_content = existing_content + mde_section
    
    # Ensure directory exists
    research_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Write updated content
    with open(research_file, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    return str(research_file)

def main():
    """Main entry point for updating research.md with MDE results."""
    # Default paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    mde_results_path = project_root / "data" / "processed" / "pilot_mde_results.json"
    research_md_path = project_root / "docs" / "research.md"
    
    if not mde_results_path.exists():
        print(f"Error: Pilot results file not found at {mde_results_path}")
        sys.exit(1)
    
    try:
        updated_path = update_research_md(str(mde_results_path), str(research_md_path))
        print(f"Successfully updated research.md at: {updated_path}")
    except Exception as e:
        print(f"Error updating research.md: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
