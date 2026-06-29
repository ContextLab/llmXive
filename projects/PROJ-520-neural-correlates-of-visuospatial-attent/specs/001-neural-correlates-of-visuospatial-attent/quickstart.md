# Quickstart: Neural Correlates of Visuospatial Attention Shifts During Simulated Navigation

## Prerequisites

- Python 3.11+
- GitHub Actions Runner (Linux, 2 CPU, 7 GB RAM)
- Access to OpenNeuro (if available per `research.md` Dataset Strategy)

## Installation

```bash
pip install -r code/requirements.txt
```

## Running the Pipeline

1. **Download Data**:
   ```bash
   python code/main.py --task download
   ```
   *Note: Will fail if OpenNeuro ds0001171 is unreachable (see `research.md`). HALTS if no verified dataset found.*

2. **Preprocess**:
   ```bash
   python code/main.py --task preprocess
   ```
   *Outputs: `data/processed/epochs.fif`*
   *Checks epoch count per SC-005; halts if <100 per condition.*

3. **Extract Features**:
   ```bash
   python code/main.py --task features
   ```
   *Outputs: `data/processed/features.csv`*
   *Applies baseline normalization (−500ms to 0ms).*

4. **Classify & Validate**:
   ```bash
   python code/main.py --task classify
   ```
   *Outputs: `data/processed/results.json`*
   *Includes participant_count, permutation results, FWE corrections.*

## Verification

- Check `data/processed/results.json` for:
  - `participant_count` (addresses plan_consistency-c63414a0)
  - Accuracy ≥65% (Constitution Principle VII benchmark)
  - p-value ≤0.05 (SC-003)
- Verify `data/` checksums against `state/` hashes.
- Confirm FWE correction applied for per-feature tests (FR-009).