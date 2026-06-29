# PROJ-488: Evaluating the Impact of Code Generation

This project evaluates the impact of code generation on code quality metrics
using static analysis tools and statistical testing.

## Setup

Run the setup script to create the project structure:
```bash
python code/setup_project.py
```

## Project Structure

- `code/` - Python source code and modules
- `data/raw/` - Raw dataset files (CodeSearchNet, CodeGen)
- `data/processed/` - Processed and filtered datasets
- `data/metrics/` - Computed metrics (CSV files)
- `results/` - Analysis results, figures, and reports
- `state/` - Pipeline state tracking YAML files
- `specs/` - Feature specifications and design documents

## Requirements

See `code/requirements.txt` for dependencies.

## Constitutional Amendments

⚠️ This project requires approval of Constitutional Amendments T009 and T010
before proceeding with Phase 3+. Check `state/projects/PROJ-488-evaluating-the-impact-of-code-generation.yaml`
for amendment status.

## License

Research project under llmXive automated science pipeline.