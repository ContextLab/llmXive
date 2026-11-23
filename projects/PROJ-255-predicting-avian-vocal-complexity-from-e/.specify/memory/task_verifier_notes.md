# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003** — The repository contains a `pyproject.toml` with Black and a minimal Ruff section, but the required `.ruff.toml` file is missing entirely, and there is no evidence that `ruff check src/` and `black --check src/` have been run successfully. The deliverable is therefore not fully satisfied.
- **T005** — The provided `src/utils/logging.py` stops mid‑definition of `log_error` (and likely never defines `log_warning`), so the required functions are missing. Additionally, the file is truncated, indicating the implementation is incomplete. The logger setup is present, but without the full error‑handling functions the deliverable is not satisfied.
- **T006** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T007** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T015d** — The repository lacks the required `data/interim/interpolated_records.csv` file, and the shown `src/data/acquisition.py` does not contain any implementation of a nearest‑neighbor interpolation routine (no function using `geopy` to search within 50 km or to write the interpolated CSV). Consequently the task’s core requirement is not satisfied.
- **T015** — The provided `src/data/acquisition.py` contains code for Xeno‑canto metadata, OSM land‑use mapping, and does not implement fetching the Global Soundscapes dataset, the fallback mirror, error handling, or merging with `interpolated_records.csv`. Moreover, the required output file `data/interim/noise_mapped.csv` (and the prerequisite `data/interim/interpolated_records.csv`) are absent. The task’s core functionality and deliverables are therefore not satisfied.
- **T015c** — declared artifact(s) missing/empty/invalid: data/interim/validation_log.csv
- **T015e** — No artifact (e.g., log file, report, or code output) showing that missing noise values within 50 km were interpolated, that failures were counted, and that a warning was logged when >10 % failed is present. Without such evidence the requirement cannot be confirmed.
