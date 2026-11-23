# PROJ-062 – Quantifying the Impact of Code Ownership

This directory contains the full source tree for the project as specified in the
implementation plan. The layout mirrors the repository‑wide layout used by the
pipeline scripts.

## Directory layout

```
code/ # Python source files (pipeline, utilities, etc.)
data/
 raw/ # Shallow‑cloned Git repositories (immutable)
 intermediate/ # CSVs generated during processing
 results/ # Final JSON reports, PNG visualisations
tests/
 unit/ # Unit tests for individual modules
 integration/ # End‑to‑end pipeline tests
docs/
 README.md # Documentation for the project
```

The folder hierarchy is created by running:

```bash
python code/scripts/setup_project.py
```

This script is idempotent – running it multiple times will not overwrite existing
files.