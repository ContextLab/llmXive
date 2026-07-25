# code/utils

This directory contains utility scripts for the llmXive pipeline.

## Modules

- `create_scene_descriptions.py`: Handles fetching real scene data from COCO or generating deterministic fallback scenes.
- `update_state.py`: Calculates SHA-256 hashes of project artifacts and updates the state file.

## Usage

### Generate Scene Descriptions
```bash
python code/utils/create_scene_descriptions.py
```
This will attempt to fetch 100 interaction scenes from the COCO Captions dataset.
If the fetch fails, it will generate a deterministic fallback set.
Output: `data/raw/scene_descriptions.csv`

### Update State
```bash
python code/utils/update_state.py
```
This scans the `data`, `code`, `tests`, and `specs` directories and updates
`state/projects/PROJ-820_state.json` with the current file hashes.