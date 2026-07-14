# Temporary Data Directory

This directory is used for intermediate files during processing.

## Usage
- Temporary cache files
- Intermediate calculation outputs
- Lock files for concurrent processes

## Cleanup
Files in this directory may be deleted at any time without affecting the project state.
The `code/ingest.py` and `code/modeling.py` scripts are responsible for cleaning up their own temporary files.