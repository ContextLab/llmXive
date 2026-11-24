# PROJ-050 – The Effect of Priming on Prosocial Behavior

This directory contains the full code, data, documentation, and results for the
research project *The Effect of Priming on Prosocial Behavior in Online Communities*.

## Directory Structure

```
PROJ-050-the-effect-of-priming-on-prosocial-behav/
├── code/ # Pipeline scripts
├── data/
│ ├── raw/ # Raw streamed data (not persisted)
│ ├── processed/ # Processed CSV/JSON outputs
│ ├── validation/ # Human‑annotation files and logs
│ └── results/ # Final result files (JSON, PNG, etc.)
├── docs/ # Documentation (dataset acquisition, feasibility, etc.)
├── specs/ # Schema contracts and analysis specifications
├── tests/
│ ├── unit/ # Unit tests
│ └── integration/ # Integration tests for the full pipeline
├── results/ # Top‑level results folder (mirrors data/results)
├── figures/ # Generated figures (symlinked from data/results if needed)
├── paper/ # Draft manuscript sections
└── logs/ # Per‑process log files
```

The layout follows the conventions defined in the project’s `tasks.md` and
`quickstart.md`. All pipeline stages read from and write to the paths
described in those documents.