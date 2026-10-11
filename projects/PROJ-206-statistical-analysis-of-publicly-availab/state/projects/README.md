# Project State Directory

This folder stores YAML manifests that track the state of the analysis pipeline.

- **`PROJ-206-statistical-analysis-of-publicly-availab.yaml`** – Contains artifact hashes, checksum maps, and any pipeline‑level flags (e.g., data‑sufficiency warnings).
- The state file is automatically updated by utility functions in `src.utils.state`.
- Do not manually edit the hashes; they are generated programmatically after each successful write operation.