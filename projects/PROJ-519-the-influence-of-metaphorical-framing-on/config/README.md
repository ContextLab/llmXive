# Project Configuration

This directory holds configuration artifacts for the metaphor-framing
attitudes research pipeline (PROJ-519).

## Contents

- `simulation_config.yaml` — pinned random seeds, synthetic data
 parameters (experimental module only), sampling thresholds
 (`corpus_size`, `MAX_RUNTIME_SECONDS`, `SAMPLE_SIZE_FALLBACK`),
 and the `USE_REAL_DATA_ONLY` flag (default: true) for the discourse
 corpus loader (see tasks T006, T021a).

## Conventions

- All configuration is version-controlled; no secrets or API keys
 belong here (use environment variables via dotenv, see T008).
- Random seeds are pinned to guarantee bit-for-bit reproducibility.
- Any new configuration keys must be documented in this README.
