# Documentation Index

This directory contains design documents, API references, and user guides for PROJ-037.

## Contents

### 1. Design Documents
- `design.md`: Overview of the research question, methodology, and constraints.
- `data-model.md`: Schema definitions for raw and processed data.
- `contracts/`: API contracts and dataset schemas (e.g., `dataset.schema.yaml`).

### 2. API Reference
- `api.md`: Detailed documentation of all modules in `code/`, including function signatures and usage examples.

### 3. User Guides
- `installation.md`: Step-by-step installation instructions.
- `pipeline.md`: Detailed walkthrough of the data pipeline (Ingestion → Analysis → Validation → Report).
- `troubleshooting.md`: Common issues and solutions.

### 4. Research Notes
- `research_question_validation.md`: Reviewer feedback on the research question (e.g., Linus Pauling's critique on correlation vs. causation).

## Notes on Scientific Rigor
All documentation adheres to the principle that **correlation is not causation**. Every report and analysis output explicitly frames findings as "associational" to comply with FR-008.

## Contributing
When updating documentation:
1. Ensure all claims are backed by code or data.
2. Avoid causal language.
3. Update the `README.md` in the root directory if major changes occur.
