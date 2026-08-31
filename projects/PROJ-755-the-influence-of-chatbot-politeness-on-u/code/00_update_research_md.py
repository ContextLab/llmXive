import json
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Ensure the code directory is in the path for relative imports if running as script
if __name__ == "__main__":
    script_dir = Path(__file__).resolve().parent
    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))

def load_pilot_results(results_path: str) -> Dict[str, Any]:
    """
    Load the pilot MDE results from the JSON file.
    
    Args:
        results_path: Path to the pilot_mde_results.json file.
        
    Returns:
        Dictionary containing the MDE results.
        
    Raises:
        FileNotFoundError: If the results file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    path = Path(results_path)
    if not path.exists():
        raise FileNotFoundError(f"Pilot results file not found: {results_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def format_mde_section(results: Dict[str, Any]) -> str:
    """
    Format the MDE results into a Markdown section.
    
    Args:
        results: Dictionary containing MDE results (minimum_detectable_effect, power, sample_size).
        
    Returns:
        Formatted Markdown string.
    """
    mde = results.get('minimum_detectable_effect', 'N/A')
    power = results.get('power', 'N/A')
    sample_size = results.get('sample_size', 'N/A')
    
    section = f"""
## MDE_Estimation

Based on the pilot analysis, the Minimum Detectable Effect (MDE) has been calculated.

- **Minimum Detectable Effect**: {mde}
- **Target Power**: {power}
- **Required Sample Size**: {sample_size}

These estimates will guide the final sample size requirements for the main study.
"""
    return section

def update_research_md(
    results_path: str,
    research_md_path: str,
    section_header: str = "MDE_Estimation"
) -> None:
    """
    Update the research.md file with the MDE estimation results.
    
    This function reads the MDE results from a JSON file, formats them into a 
    Markdown section, and appends this section to the research.md file under 
    the specified header.
    
    Args:
        results_path: Path to the pilot_mde_results.json file.
        research_md_path: Path to the research.md file to update.
        section_header: The header name to look for or create in research.md.
    """
    # Load results
    results = load_pilot_results(results_path)
    
    # Format section
    mde_section = format_mde_section(results)
    
    # Ensure research.md exists
    md_path = Path(research_md_path)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    
    content = ""
    if md_path.exists():
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
    
    # Check if section header exists
    header_marker = f"## {section_header}"
    
    if header_marker in content:
        # Find the start of the section
        start_idx = content.find(header_marker)
        # Find the start of the next section (if any)
        next_header_idx = content.find("\n## ", start_idx + len(header_marker))
        
        if next_header_idx == -1:
            # No next section, replace from header to end
            new_content = content[:start_idx] + mde_section
        else:
            # Replace content between this header and the next
            new_content = content[:start_idx] + mde_section + "\n" + content[next_header_idx:]
    else:
        # Append new section at the end
        if content and not content.endswith('\n'):
            content += '\n'
        new_content = content + mde_section.lstrip('\n')
    
    # Write back
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

def main() -> None:
    """
    Main entry point for updating research.md with MDE results.
    """
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    results_file = project_root / "data" / "processed" / "pilot_mde_results.json"
    research_file = project_root / "research.md"
    
    if not results_file.exists():
        print(f"Error: Pilot results file not found at {results_file}")
        print("Please ensure T011b3 has completed successfully.")
        sys.exit(1)
    
    try:
        update_research_md(
            results_path=str(results_file),
            research_md_path=str(research_file)
        )
        print(f"Successfully updated {research_file} with MDE estimation results.")
    except Exception as e:
        print(f"Error updating research.md: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()