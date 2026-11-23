# Report Templates

This directory contains Jinja2 templates for automated report generation.

## Templates

- `paper_template.md.j2`: Main template for generating the meta-analysis paper draft.

## Usage

The `report_generator.py` module loads templates from this directory and renders them with the `MetaAnalysisResult` JSON data to produce `docs/paper_draft.md`.

## Template Variables

The template has access to:
- `generated_at`: ISO format timestamp of generation
- `result`: The entire `MetaAnalysisResult` dictionary

## Customization

To modify the report format, edit the template files in this directory. Ensure the template uses valid Jinja2 syntax and references keys that exist in the `MetaAnalysisResult` schema.