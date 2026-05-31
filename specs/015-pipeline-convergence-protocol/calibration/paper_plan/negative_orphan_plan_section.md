# Plan — synthetic seed (calibration positive)

## Methodology
Compare clean-vs-injected verdicts per stage, repeated for noise-
robustness. Use the differential calibration adjudication report as the
single source of truth for prompt-adjustment decisions.

## Datasets
- llmXive evaluation traces (already on disk; no external download).
- The 9 anchor papers from `llmxive.calibration.domains` (DOIs in the
  module; manual lookup required at T068 adjudication).

## Plan ↔ data-model coherence
The CalibrationRun dataclass mirrors the FR-001/FR-002 fields exactly.

## Constitution Check
- Principle V (real-call testing): satisfied by T068 real-qwen runs.
- Principle II (honest reporting): satisfied by the "missed injection
  → false negative" surface in the report.


## Real-time deployment evaluation (INJECTED)

We add a section evaluating end-to-end latency on production workloads (this plan section is deliberately fabricated for calibration — the paper spec does not mention real-time or deployment evaluation).