import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from utils.config import get_project_root, ensure_directory
from utils.logger import get_logger

try:
    from jinja2 import Environment, FileSystemLoader, TemplateNotFound
except ImportError:
    raise ImportError(
        "Jinja2 is required for report generation. "
        "Please install it via 'pip install jinja2'."
    )

logger = get_logger(__name__)

def load_meta_analysis_result(
    json_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Load the meta-analysis result from a JSON file.

    Args:
        json_path: Path to the results JSON file. If None, uses the default
                   path from project configuration.

    Returns:
        Dictionary containing the meta-analysis results.

    Raises:
        FileNotFoundError: If the results file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    if json_path is None:
        project_root = get_project_root()
        json_path = project_root / "data" / "derived" / "results.json"

    if not json_path.exists():
        raise FileNotFoundError(f"Results file not found: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

def render_paper_draft(
    results: Dict[str, Any],
    template_name: str = "paper_draft.md.jinja2",
    output_path: Optional[Path] = None,
) -> Path:
    """
    Render the paper draft using a Jinja2 template and the meta-analysis results.

    Args:
        results: The meta-analysis results dictionary.
        template_name: Name of the Jinja2 template file.
        output_path: Path to write the generated markdown file. If None,
                     uses the default path.

    Returns:
        Path to the generated paper draft.

    Raises:
        TemplateNotFound: If the specified template does not exist.
    """
    project_root = get_project_root()

    # Set up Jinja2 environment
    template_dir = project_root / "templates"
    ensure_directory(template_dir)
    env = Environment(loader=FileSystemLoader(str(template_dir)))

    try:
        template = env.get_template(template_name)
    except TemplateNotFound:
        # Create a default template if one doesn't exist
        logger.warning(
            f"Template '{template_name}' not found. Creating a default template."
        )
        default_template_content = """
# Structural Brain Connectivity and Music Preferences: Meta-Analysis Report

## Executive Summary

**Synthesis Mode**: {{ results.get('synthesis_mode', 'N/A') }}
**Study Count**: {{ results.get('N', 'N/A') }}
**Timestamp**: {{ results.get('timestamp', 'N/A') }}

{% if results.get('synthesis_mode') == 'quantitative' %}
## Quantitative Results

### Pooled Effect Size
- **Weighted Mean r**: {{ "%.4f"|format(results.get('weighted_mean_r', 0)) }}
- **95% CI**: [{{ "%.4f"|format(results.get('ci_lower', 0)) }}, {{ "%.4f"|format(results.get('ci_upper', 0)) }}]
- **Model Type**: {{ results.get('model_type', 'Random Effects') }}

### Heterogeneity
- **I² Statistic**: {{ results.get('i_squared', 'N/A') }}
- **Egger's Test p-value**: {{ results.get('egger_p', 'N/A') }}

### Multiple Comparison Correction
- **Bonferroni Applied**: {{ results.get('bonferroni_applied', False) }}
{% if results.get('bonferroni_applied') %}
- **Adjusted Threshold**: {{ results.get('adjusted_threshold', 'N/A') }}
{% endif %}
{% endif %}

{% if results.get('synthesis_mode') == 'narrative' %}
## Narrative Synthesis

### Study Overview
{{ results.get('narrative_overview', 'No overview available.') }}

### Qualitative Themes
{% for theme in results.get('narrative_themes', []) %}
- **{{ theme.get('name', 'Unnamed') }}**: {{ theme.get('description', 'No description') }} ({{ theme.get('count', 0) }} studies)
{% endfor %}

### Limitations
{{ results.get('limitations', 'Insufficient data for quantitative analysis (N < 10).') }}
{% endif %}

## Conclusions

{% if results.get('synthesis_mode') == 'quantitative' and results.get('weighted_mean_r', 0) > 0.3 %}
The meta-analysis indicates a **moderate positive correlation** between structural brain
connectivity and individual music preferences.
{% elif results.get('synthesis_mode') == 'quantitative' %}
The meta-analysis indicates a **weak or negligible correlation** between structural brain
connectivity and individual music preferences.
{% else %}
Due to insufficient studies (N < 10), a quantitative meta-analysis was not possible.
The narrative synthesis suggests preliminary patterns that warrant further investigation.
{% endif %}

---
*Generated automatically by llmXive on {{ results.get('timestamp', datetime.now().isoformat()) }}*
"""
        default_template_path = template_dir / template_name
        with open(default_template_path, "w", encoding="utf-8") as f:
            f.write(default_template_content)
        template = env.get_template(template_name)

    # Render the template
    rendered_content = template.render(results=results, datetime=datetime)

    # Determine output path
    if output_path is None:
        docs_dir = project_root / "docs"
        ensure_directory(docs_dir)
        output_path = docs_dir / "paper_draft.md"
    else:
        ensure_directory(output_path.parent)

    # Write the output
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(rendered_content)

    logger.info(f"Paper draft generated: {output_path}")
    return output_path

def run_report_generation(
    results_path: Optional[Path] = None,
    template_name: str = "paper_draft.md.jinja2",
    output_path: Optional[Path] = None,
) -> Path:
    """
    Main entry point for report generation.

    Args:
        results_path: Path to the results JSON file.
        template_name: Name of the Jinja2 template.
        output_path: Path for the output markdown file.

    Returns:
        Path to the generated paper draft.
    """
    logger.info("Starting report generation...")

    # Load results
    results = load_meta_analysis_result(results_path)

    # Render paper draft
    output = render_paper_draft(results, template_name, output_path)

    logger.info("Report generation complete.")
    return output

def main():
    """Command-line entry point for report generation."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate paper draft from meta-analysis results."
    )
    parser.add_argument(
        "--results",
        type=Path,
        default=None,
        help="Path to results JSON file (default: data/derived/results.json)",
    )
    parser.add_argument(
        "--template",
        type=str,
        default="paper_draft.md.jinja2",
        help="Jinja2 template name (default: paper_draft.md.jinja2)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output path for paper draft (default: docs/paper_draft.md)",
    )

    args = parser.parse_args()

    try:
        output_path = run_report_generation(
            results_path=args.results,
            template_name=args.template,
            output_path=args.output,
        )
        print(f"Paper draft generated successfully: {output_path}")
        return 0
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in results file: {e}")
        return 1
    except Exception as e:
        logger.error(f"Error during report generation: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())