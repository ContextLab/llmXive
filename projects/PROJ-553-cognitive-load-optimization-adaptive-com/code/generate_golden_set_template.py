"""
Generate the Golden Set Template for expert labeling.

This script creates a CSV template with 'interaction_id' and an empty
'expert_load_score' column, along with a README for domain experts.
"""
import os
import sys
import csv
from pathlib import Path

# Ensure we can import from the project root if run as a script
if __name__ == "__main__":
    # Add parent directory to path if running directly
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

def generate_template(output_dir: Path) -> Path:
    """
    Generate the golden set template CSV.

    Args:
        output_dir: Directory to save the template.

    Returns:
        Path to the generated CSV file.
    """
    template_path = output_dir / "golden_set_template.csv"

    # Define columns
    columns = ["interaction_id", "expert_load_score"]

    # Write empty template with headers only
    with open(template_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(columns)

    print(f"Template created at: {template_path}")
    return template_path

def generate_readme(output_dir: Path) -> Path:
    """
    Generate a README file with instructions for domain experts.

    Args:
        output_dir: Directory to save the README.

    Returns:
        Path to the generated README file.
    """
    readme_path = output_dir / "README_EXPERT_INSTRUCTIONS.md"

    instructions = """# Golden Set Labeling Instructions

## Purpose
This document provides instructions for domain experts to label interactions in the 
`golden_set_template.csv` file to create the validation dataset for the Cognitive Load 
Estimation Model.

## Background
The Golden Set is a critical component of our research pipeline. It serves as the 
ground truth against which our model's predictions are validated. Unlike self-reported 
metrics (which risk the "illusion of competence"), this set relies on expert judgment 
of cognitive load based on behavioral proxies (latency, errors, hints).

## Instructions

1. **Download the Template**: Open `golden_set_template.csv` in your preferred 
   spreadsheet editor (Excel, Google Sheets, etc.).

2. **Review the Data**: The template contains a list of `interaction_id`s derived 
   from real student interaction logs (ASSISTments/OULAD datasets). Each row represents 
   a single learning interaction.

3. **Assign Load Scores**: For each `interaction_id`, assign an `expert_load_score` 
   ranging from **0 to 100**.
   - **0**: Minimal cognitive load (e.g., immediate correct answer, no hesitation).
   - **50**: Moderate cognitive load (e.g., some hesitation, minor errors, standard help requests).
   - **100**: High cognitive load (e.g., significant struggle, multiple errors, extensive help requests, long latency).

4. **Criteria for Scoring**:
   - **Latency**: Longer time spent on a problem generally indicates higher load.
   - **Errors**: Multiple incorrect attempts suggest higher load.
   - **Hints**: Frequent hint requests indicate the student is struggling to retrieve knowledge.
   - **Context**: Consider the difficulty of the specific skill being tested.

5. **Minimum Requirements**: 
   - You must label **at least 50 interactions**.
   - Ensure scores are integers between 0 and 100.
   - Do not leave any `expert_load_score` cells empty in the final submission.

6. **Save and Submit**: 
   - Save the file as `golden_set.csv` (overwriting the template name is acceptable 
     if the original template is backed up).
   - Ensure the file format remains CSV.
   - Place the file in the `data/processed/` directory.

## Important Notes
- **No Synthetic Data**: Do not generate fake scores. Your expert judgment is required.
- **Consistency**: Try to maintain a consistent standard across all 50+ items.
- **Anonymity**: The `interaction_id`s are anonymized; do not attempt to identify specific students.

## Validation
Once submitted, the file will be validated to ensure:
- It contains at least 50 rows (excluding the header).
- All `expert_load_score` values are valid numbers between 0 and 100.
- No rows have missing scores.

If validation fails, the pipeline will halt with a clear error message.

## Contact
If you have questions about specific scoring criteria, please consult the project 
research lead or refer to the `docs/research.md` file for detailed methodology.
"""

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(instructions)

    print(f"README created at: {readme_path}")
    return readme_path

def main():
    """Main entry point to generate the template and README."""
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Generating Golden Set Template...")
    generate_template(output_dir)
    generate_readme(output_dir)
    print("Done. Please distribute the template and README to domain experts.")

if __name__ == "__main__":
    main()