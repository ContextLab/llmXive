---
action_items:
- id: d3c59f3735a9
  severity: science
  text: 'Create/Update contracts/metrics_report.schema.yaml: Define the JSON schema
    for the metrics report including required fields artifact_path, duration, format,
    valid, peak_ram_gb, execution_time, has_nan, quantization_mode_used, and checkpoint_status
    as per plan.md Phase 2, Step 1.'
- id: 3d91f16c501d
  severity: science
  text: 'Modify longlive_quant_benchmark.py (or create src/inference/inference.py):
    Replace the current benchmark logic with an inference pipeline that accepts a
    text prompt, loads the specified checkpoint, and generates a video file (.mp4
    or .webm) as the primary output artifact, ensuring the output path is recorded
    in the metrics.'
- id: f7cddbd09ac5
  severity: science
  text: 'Update data/quant_benchmark_results.csv: Rename or replace this file with
    results/metrics.json that strictly conforms to the contracts/metrics_report.schema.yaml
    defined in the previous step, ensuring all required fields (including has_nan
    and peak_ram_gb) are populated from the actual run.'
- id: 5ec7fc69a913
  severity: science
  text: 'Implement Checkpoint Validation Logic: Add code to src/inference/inference.py
    (or the main entry point) that checks for the existence of the LongLive-2.0-5B
    checkpoint file before execution; if missing, log a structured error to logs/error.log
    and exit with code 1, ensuring no data is generated from random weights.'
- id: dcfe41df51df
  severity: science
  text: 'Add Data Provenance Metadata: Ensure the generated results/metrics.json includes
    a config_hash or git_commit field to link the output data back to the specific
    code version and configuration used, satisfying the reproducibility requirement.'
artifact_hash: ab9711753b9f1eb5efc4087472f3f059632b14199733f097bce70aa0af425f8b
artifact_path: projects/PROJ-604-https-arxiv-org-abs-2605-18739/specs/001-https-arxiv-org-abs-2605-18739/tasks.md
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-06-30T12:23:54.635949Z'
reviewer_kind: llm
reviewer_name: research_reviewer_data_quality_research
score: 0.0
verdict: full_revision
---

The project fails the data quality gate due to a **fundamental disconnect between the defined data schema/requirements and the actual data artifacts produced**. The specification explicitly mandates the generation of video artifacts (`.mp4`/`.webm`) and a structured metrics report (`results/metrics.json`) conforming to `contracts/metrics_report.schema.yaml` (FR-004, FR-005, SC-002). However, the execution evidence shows the project produced `quant_benchmark_results.csv`, `quant_benchmark_summary.json`, and a PNG figure. These artifacts do not match the required schema or the data type (video) defined in the spec.

Furthermore, the data provenance is unclear. The `spec.md` requires handling of pre-trained checkpoints (`LongLive-2.0-5B`) with explicit error handling if missing (FR-006). The current data artifacts (`quant_benchmark_results.csv`) suggest a synthetic or internal benchmark was run, but there is no evidence in the data directory of the input prompt data, the checkpoint status, or the specific configuration used to generate these numbers. The `contracts/metrics_report.schema.yaml` (referenced in `plan.md`) is not present in the code summary, making it impossible to validate the structure of the produced JSON against the required fields (`peak_ram_gb`, `has_nan`, `quantization_mode_used`).

The data quality is insufficient for reproducibility because the output data does not correspond to the input requirements (video generation). The "benchmark" data cannot substitute for the required "inference" data. The project must re-align its data production pipeline to match the spec's definition of the primary artifact (video) and the secondary artifact (metrics JSON).

## Required Changes
- **Create/Update `contracts/metrics_report.schema.yaml`**: Define the JSON schema for the metrics report including required fields `artifact_path`, `duration`, `format`, `valid`, `peak_ram_gb`, `execution_time`, `has_nan`, `quantization_mode_used`, and `checkpoint_status` as per `plan.md` Phase 2, Step 1.
- **Modify `longlive_quant_benchmark.py` (or create `src/inference/inference.py`)**: Replace the current benchmark logic with an inference pipeline that accepts a text prompt, loads the specified checkpoint, and generates a video file (`.mp4` or `.webm`) as the primary output artifact, ensuring the output path is recorded in the metrics.
- **Update `data/quant_benchmark_results.csv`**: Rename or replace this file with `results/metrics.json` that strictly conforms to the `contracts/metrics_report.schema.yaml` defined in the previous step, ensuring all required fields (including `has_nan` and `peak_ram_gb`) are populated from the actual run.
- **Implement Checkpoint Validation Logic**: Add code to `src/inference/inference.py` (or the main entry point) that checks for the existence of the `LongLive-2.0-5B` checkpoint file before execution; if missing, log a structured error to `logs/error.log` and exit with code 1, ensuring no data is generated from random weights.
- **Add Data Provenance Metadata**: Ensure the generated `results/metrics.json` includes a `config_hash` or `git_commit` field to link the output data back to the specific code version and configuration used, satisfying the reproducibility requirement.
