# Implementation Plan: llmXive follow-up: extending "MolmoMotion: Forecasting Point Trajectories in 3D with Language Instru"

**Branch**: `001-llmxive-motion-scaling` | **Date**: 2026-09-05 | **Spec**: `specs/001-llmxive-follow-up-extending-molmomotion/spec.md`
**Input**: Feature specification from `/specs/001-llmxive-follow-up-extending-molmomotion/spec.md`

## Summary

This feature implements a computationally feasible, CPU-only experimental pipeline to evaluate the trade-off between instruction precision and model capacity in 3D trajectory forecasting. The system subsamples the MolmoMotion-1M corpus, synthesizes dual-modality instructions (coarse natural language vs. structured kinematic parameters) for each trajectory, and executes a lightweight **Dual-Head Linear Baseline** model. The primary goal is to measure the Average Trajectory Error (ATE) and **Instruction Adherence Score** difference between the two instruction modalities under strict resource constraints (7GB RAM, 2 CPU cores, 6h runtime) and determine statistical significance via a paired t-test.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU-only), `datasets` (Hugging Face), `pandas`, `scikit-learn`, `numpy`, `pyyaml`  
**Storage**: Local filesystem (temporary RAM-disk or disk-based streaming to stay under 7GB), `data/` directory for artifacts  
**Testing**: `pytest` (unit tests for data synthesis, integration tests for pipeline execution)  
**Target Platform**: GitHub Actions Free Tier (Linux, 2 vCPU, 7GB RAM), CPU-only execution enforced  
**Project Type**: Computational Research Pipeline / CLI  
**Performance Goals**: Process [deferred] trajectory instances within 6 hours; peak RAM ≤ 7GB; no GPU access.  
**Constraints**: Strict CPU enforcement (`torch.set_device('cpu')`); streaming data loading; deterministic random seeds; no synthetic data generation (must use real subsampled data).  
**Scale/Scope**: Subsampled subset of MolmoMotion-1M (target: [deferred] instances); dual instruction generation per instance; paired statistical analysis.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*Gates determined based on `projects/PROJ-848-llmxive-follow-up-extending-molmomotion/.specify/memory/constitution.md`*

- **I. Reproducibility**: ✅ PASS. The plan enforces pinned random seeds in `code/`, uses canonical Hugging Face dataset URLs for MolmoMotion, and mandates a `requirements.txt` with pinned versions. The pipeline is designed to run end-to-end on a fresh CI runner.
- **II. Verified Accuracy**: ✅ PASS. All dataset citations reference the verified URLs in the `# Verified datasets` block (MolmoMotion processed trajectories). No unverified URLs are introduced.
- **III. Data Hygiene**: ✅ PASS. The plan specifies checksumming raw data downloads in `data/`, preserving raw files, and writing derived artifacts (subsampled data, predictions) to new filenames with documented derivation steps.
- **IV. Single Source of Truth**: ✅ PASS. The pipeline outputs a structured results file (JSON/CSV) containing all ATE values, Adherence Scores, and test statistics. The analysis script reads *only* from this file, ensuring the paper figures trace back to this single artifact.
- **V. Versioning Discipline**: ✅ PASS. The plan includes a step to record content hashes of all artifacts in the project state file.
- **VI. CPU-Only Inference Fidelity**: ✅ PASS. The plan explicitly mandates `torch.set_device('cpu')` and includes a runtime check to verify no GPU is accessed. The model architecture is chosen to be CPU-tractable.
- **VII. Dual-Modal Instruction Verification**: ✅ PASS. The data synthesis phase (FR-002) is designed to generate both "coarse" NL and "structured" kinematic instructions for *every* trajectory instance. The plan explicitly includes the calculation of the **Instruction Adherence Score** (in addition to ATE) to satisfy the constitutional requirement for quantifying the trade-off between semantic precision and model capacity.

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-motion-scaling/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── prediction.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-848-llmxive-follow-up-extending-molmomotion/
├── data/
│   ├── raw/                  # Downloaded MolmoMotion artifacts (parquet, jsonl)
│   ├── processed/            # Subsampled parquet, instruction pairs
│   └── results/              # Prediction outputs, ATE metrics, t-test results
├── code/
│   ├── requirements.txt      # Pinned dependencies
│   ├── src/
│   │   ├── __init__.py
│   │   ├── data_loader.py    # Streaming download, subsampling
│   │   ├── instruction_synthesizer.py # NL + Kinematic generation
│   │   ├── model.py          # Dual-Head Linear Model (CPU)
│   │   ├── inference.py      # Batch inference loop
│   │   ├── metrics.py        # ATE + Adherence Score calculation
│   │   └── analysis.py       # Paired t-test, reporting
│   ├── tests/
│   │   ├── test_data_loader.py
│   │   ├── test_synthesis.py
│   │   └── test_metrics.py
│   └── run_pipeline.sh       # Orchestration script
└── state/
    └── projects/PROJ-848-llmxive-follow-up-extending-molmomotion.yaml
```

**Structure Decision**: Single project structure selected. The pipeline is a linear research workflow (Download -> Synthesize -> Infer -> Analyze) rather than a multi-service architecture. This minimizes overhead and fits the 7GB RAM constraint by keeping state in local variables and streaming data.

### Schema Mapping

To ensure internal coherence, the following mapping links pipeline phases to the contract schemas:

| Pipeline Phase | Output Artifact | Contract Schema | Key Fields Produced |
| :--- | :--- | :--- | :--- |
| **Subsampling** | `data/processed/subsampled_instances.parquet` | `dataset.schema.yaml` | `instance_id`, `ground_truth_points`, `kinematic_metadata` |
| **Synthesis** | `data/processed/instruction_pairs.jsonl` | `dataset.schema.yaml` | `instruction_nl`, `instruction_struct`, `synthesis_status`, `nl_embedding_vector` (BoW) |
| **Inference** | `data/results/predictions.jsonl` | `prediction.schema.yaml` | `predicted_points`, `ate`, `adherence_score`, `instruction_type`, `status` |
| **Analysis** | `data/results/ate_comparison.csv` | N/A (Aggregated) | `mean_ate_nl`, `mean_ate_struct`, `mean_adherence_nl`, `mean_adherence_struct`, `p_value` |

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Dual Instruction Synthesis | Required to test the core hypothesis (Precision vs. Capacity). | A single instruction modality would fail to address FR-002 and the research question. |
| Streaming Data Loading | Essential to fit MolmoMotion-1M subsample within 7GB RAM. | Loading the full dataset into memory would cause OOM on the CI runner. |
| Paired Statistical Design | Required for FR-005 to control for trajectory variance. | An unpaired t-test would have lower power and fail to isolate the instruction effect. |
| Dual-Head Linear Model | Required to isolate the effect of input precision without complex embeddings. | A single model with a text encoder would exceed CPU/RAM limits or introduce confounds. |