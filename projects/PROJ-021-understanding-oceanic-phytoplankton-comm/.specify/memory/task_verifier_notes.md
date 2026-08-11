# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T009** — The provided `tests/contract/test_schemas.py` exists but is truncated and references a non‑existent `aligned_dataset.schema.yaml`; without the schema file the contract test cannot perform any validation. The required schema artifact is missing, so the task’s requirement is not met.
- **T011a** — The required output file `data/raw/reanalysis.nc` does not exist on disk, so the reanalysis data was not fetched and saved as specified. The task’s core requirement is therefore unmet.
- **T011b** — The required output file `data/raw/modis.nc` does not exist, so the MODIS data was not fetched and saved as specified. The task’s core requirement is unmet.
- **T011** — The required output file `data/raw/seabass.csv` does not exist, so no data was fetched or saved. Without this artifact the task’s core requirement is unmet.
- **T012** — The provided `code/02_preprocessing.py` is truncated and does not show implementation of linear interpolation for ≤2‑month gaps, error quantification, or flagging of larger gaps. Moreover, the required `data/logs/interpolation_error.log` file is absent. The task’s core requirements are therefore not satisfied.
- **T013** — The provided `code/02_preprocessing.py` snippet shows only data loading, grid coarsening, and a partially‑implemented composite function; there is no evidence of basin stratification, unified masking across the three data sources, or exclusion of cells missing in‑situ data. Moreover, the required log file `data/logs/memory_enforcement.log` does not exist, indicating that memory‑usage monitoring and enforcement were not implemented. The task therefore remains unfinished.
- **T014** — declared artifact(s) missing/empty/invalid: data/processed/aligned_dataset.nc
- **T020** — declared artifact(s) missing/empty/invalid: data/artifacts/model_comparison.csv
