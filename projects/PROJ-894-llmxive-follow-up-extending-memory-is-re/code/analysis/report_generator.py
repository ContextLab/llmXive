"""
Report Generator for llmXive Memory Reconstruction Study.

This module auto-generates docs/results.md strictly from data/processed/stats_report.json
using a Jinja2 template. No hand-typed numbers are allowed.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
except ImportError:
    raise ImportError(
        "Jinja2 is required for report generation. "
        "Install it via: pip install jinja2"
    )


def load_stats_report(report_path: Path) -> Dict[str, Any]:
    """
    Load and validate the stats report JSON.
    
    Args:
        report_path: Path to the stats_report.json file
        
    Returns:
        Dictionary containing the statistical analysis results
        
    Raises:
        FileNotFoundError: If the report file doesn't exist
        json.JSONDecodeError: If the file is not valid JSON
    """
    if not report_path.exists():
        raise FileNotFoundError(
            f"Stats report not found at {report_path}. "
            "Run the analysis scripts (T024a, T024b, T025, T027) first."
        )
    
    with open(report_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data


def generate_report(
    stats_data: Dict[str, Any],
    template_dir: Path,
    output_path: Path
) -> None:
    """
    Generate the results markdown report from stats data using a Jinja2 template.
    
    Args:
        stats_data: The statistical analysis results dictionary
        template_dir: Directory containing the Jinja2 template
        output_path: Path where the generated markdown file will be saved
    """
    # Setup Jinja2 environment
    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(['html', 'xml', 'md']),
        trim_blocks=True,
        lstrip_blocks=True
    )
    
    template = env.get_template('results_template.md.j2')
    
    # Render the template with stats data
    rendered_content = template.render(
        stats=stats_data,
        report_title="llmXive: Memory Reconstruction Analysis Results",
        generated_from="data/processed/stats_report.json"
    )
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write the report
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(rendered_content)
    
    print(f"Report generated successfully at: {output_path}")


def main():
    """
    Main entry point for the report generator.
    """
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent.parent
    stats_report_path = project_root / "data" / "processed" / "stats_report.json"
    template_dir = project_root / "code" / "analysis" / "templates"
    output_path = project_root / "docs" / "results.md"
    
    # Validate input exists
    if not stats_report_path.exists():
        print(f"Error: Stats report not found at {stats_report_path}")
        print("Please run the analysis scripts (T024a, T024b, T025, T027) first.")
        return 1
    
    # Ensure template directory exists
    if not template_dir.exists():
        print(f"Error: Template directory not found at {template_dir}")
        print("Please create the template file: code/analysis/templates/results_template.md.j2")
        return 1
    
    try:
        # Load stats data
        stats_data = load_stats_report(stats_report_path)
        
        # Generate report
        generate_report(stats_data, template_dir, output_path)
        
        return 0
        
    except FileNotFoundError as e:
        print(f"File Error: {e}")
        return 1
    except json.JSONDecodeError as e:
        print(f"JSON Error: Invalid JSON in stats report - {e}")
        return 1
    except Exception as e:
        print(f"Unexpected Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
