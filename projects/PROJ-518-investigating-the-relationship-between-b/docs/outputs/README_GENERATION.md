# Documentation Generation Guide

This guide explains how the documentation artifacts for PROJ-518 were generated and maintained.

## Purpose
The `README.md` and `docs/outputs/` directory serve as the primary interface for users to understand the pipeline, its outputs, and how to reproduce the analysis.

## Content Sources
- **README.md**: Written to reflect the current state of the codebase, including the correct paths to scripts, data directories, and output files. It is updated whenever significant new features or file paths are introduced.
- **docs/outputs/ARTIFACT_MANIFEST.md**: Created to provide a detailed inventory of the generated data and figures. This ensures that users know exactly what to expect in the `data/interim` and `docs/outputs` directories.
- **docs/outputs/README_GENERATION.md**: This file itself, documenting the documentation strategy.

## Maintenance
- When new analysis scripts are added, update `README.md` in the "Usage" and "Generated Artifacts" sections.
- When new output files are produced (e.g., new plot types), add an entry to `ARTIFACT_MANIFEST.md`.
- Ensure all file paths in documentation match the actual project structure (relative to project root).

## Verification
Run `python code/scripts/verify_sensitivity.py` to ensure that the sensitivity analysis outputs are present and valid. The documentation assumes these files exist as described.
