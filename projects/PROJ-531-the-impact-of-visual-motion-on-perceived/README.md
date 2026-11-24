# The Impact of Visual Motion on Perceived Agency in Virtual Interactions

**Feature Branch:** `001-visual-motion-agency`

This repository implements an automated research pipeline that investigates how visual motion characteristics of virtual avatars influence users' perceived sense of agency. The pipeline is designed to first attempt real‑data acquisition; if no validated dataset is available, it falls back to a synthetic data stress‑test while adhering to strict ethical guidelines.

## Quick‑Start

- See the [quickstart guide](quickstart.md) for installation instructions and a single command to run the full pipeline.
- The project scope and ethics declaration are detailed in the [Scope document](docs/scope.md).

## Repository Structure

```
├── code/ # All pipeline scripts
├── data/ # Raw, processed, and results data
├── docs/ # Documentation (including scope)
├── protocols/ # IRB approval documents (placeholder for synthetic mode)
├── quickstart.md # How to install and run the pipeline
└── README.md # This file
```

## Ethical Note

The current implementation runs in **synthetic‑only mode** (no human subjects). See the Scope document for a full ethics statement and the placeholder IRB approval file.
