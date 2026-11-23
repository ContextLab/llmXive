# Implementation Notes for PROJ-471

## Data Integrity
- **No Synthetic Data**: All data is fetched from real sources (OpenNeuro/Hugging Face).
- **Fail Loudly**: If a real data fetch fails, the script raises an error. No fallback to mock data is permitted.

## Compute Constraints
- **CPU Only**: DeepGaze II is forced to CPU mode (`device='cpu'`).
- **Memory Limit**: Scripts monitor RSS memory via `psutil`. Warnings are logged if usage exceeds 6.5GB.
- **Streaming**: Large datasets are processed in chunks or via streaming to avoid OOM errors.

## Governance Compliance
- **SCR-001**: Only "Face" ROIs are segmented. "Weapons" are excluded.
- **SCR-002**: Low-level features are computed for diagnostics only, not used in LMM.
- **SCR-003**: GBVS is the approved fallback for DeepGaze II.

## Artifact Provenance
- All generated artifacts (salience maps, metrics, results) include a SHA-256 hash and generation timestamp.
- `state.yaml` tracks the lineage of all artifacts.

## Error Handling
- **DeepGaze II Failure**: Triggers GBVS fallback. If GBVS also fails, the image is excluded and logged.
- **Missing Fixations**: Trials with missing fixation data are excluded and logged.
- **Power Gate**: If statistical power < 0.8, the pipeline halts before LMM fitting.
