# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T007** — Checked `src/data/download.py` – it defines SHA‑256 calculation and writes a metadata YAML, but it writes to `data/raw/metadata.yaml` (via `raw_dir / "metadata.yaml"`), not to the required `data/metadata.yaml`. Moreover, the repository contains no `data/metadata.yaml` file, so the required output artifact is missing. The task’s core deliverable is therefore not satisfied.
- **T009b** — The provided `src/cli/run_analysis.py` only contains placeholder phase routing and uses a config that limits processing to a regional domain (20°‑60° N, 100°‑300° E). It does not implement any domain‑filtering logic, nor does it perform streaming or chunked processing of the full global grid (90° S‑90° N, 180° W‑180° E) required by FR‑009. The task’s core functionality is therefore missing.
- **T019** — declared artifact(s) missing/empty/invalid: src/data/analysis.py
- **T020** — declared artifact(s) missing/empty/invalid: src/data/analysis.py
- **T022** — declared artifact(s) missing/empty/invalid: src/data/analysis.py
- **T023a** — declared artifact(s) missing/empty/invalid: src/data/analysis.py
- **T023b** — declared artifact(s) missing/empty/invalid: src/data/analysis.py
- **T025** — declared artifact(s) missing/empty/invalid: tests/integration/test_viz.py
- **T026** — declared artifact(s) missing/empty/invalid: src/viz/maps.py
- **T027** — declared artifact(s) missing/empty/invalid: src/viz/maps.py
- **T028** — declared artifact(s) missing/empty/invalid: src/viz/maps.py
- **T029** — declared artifact(s) missing/empty/invalid: src/viz/maps.py
- **T031** — declared artifact(s) missing/empty/invalid: src/data/analysis.py
- **T032** — declared artifact(s) missing/empty/invalid: src/data/analysis.py
- **T033** — declared artifact(s) missing/empty/invalid: src/data/analysis.py
- **T034** — declared artifact(s) missing/empty/invalid: src/data/analysis.py
- **T035** — declared artifact(s) missing/empty/invalid: src/data/analysis.py
- **T036** — declared artifact(s) missing/empty/invalid: src/data/analysis.py, data/processed/sensitivity_summary.csv
- **T038** — declared artifact(s) missing/empty/invalid: logs/performance.yaml
- **T045** — declared artifact(s) missing/empty/invalid: src/data/analysis.py
- **T046** — declared artifact(s) missing/empty/invalid: src/data/analysis.py
