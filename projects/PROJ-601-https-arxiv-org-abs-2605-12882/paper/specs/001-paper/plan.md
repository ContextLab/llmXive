# Implementation Plan: CiteVQA Reproduction & Validation Paper

**Branch**: `601-paper-citevqa-validation` | **Date**: 2026-06-30 | **Spec**: `projects/PROJ-601-https-arxiv-org-abs-2605-12882/specs/001-https-arxiv-org-abs-2605-12882/spec.md`

## Summary

This plan governs the production of the CiteVQA Reproduction & Validation Paper. The primary requirement is to demonstrate that the CiteVQA benchmark can be reproduced on free-tier CPU hardware while exposing the "Attribution Hallucination" bias (WYSIATI) via the Strict Attributed Accuracy (SAA) metric. The technical approach involves executing a modular pipeline (`infer/run.py`, `eval/run.py`, `data/validate_dataset.py`) to generate machine-readable artifacts (`outputs/evaluation_report.json`, `outputs/validation_log.json`) which serve as the direct source for all paper figures and statistical claims.

## Technical Context

**Language/Version**: Python 3.11 (Runtime), LaTeX 2e (Paper Authoring)
**Primary Dependencies**: `transformers>=4.40.0`, `torch>=2.2.0` (CPU-only), `matplotlib>=3.8.0`, `seaborn>=0.13.0`, `pandas>=2.2.0`, `pyyaml>=6.0.1`
**Storage**: Local file system (`outputs/`, `data/`); No external database.
**Testing**: `pytest` (for pipeline contract validation), `pdflatex` (for paper build gate).
**Target Platform**: Linux (CPU-only runners, <7 GB RAM constraint).
**Project Type**: Reproduction Paper / Benchmark Validation.
**Performance Goals**: Reproducible SAA score within ±0.01 of reported value; Pipeline execution < 2 hours on standard CPU.
**Constraints**: Strict CPU-only inference (no CUDA calls); Memory usage < 7 GB; No proprietary data.
**Scale/Scope**: Single benchmark subset (CiteVQA); A substantial number of samples (subject to dataset validation exclusions).

> Empirical specifics (exact sample counts, final SAA scores) are deferred to the execution of the validation pipeline.

## Constitutional Principles Compliance

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **[PASS] Principle I (SSoT)**: The plan defines a strict "Results" section structure requiring data-driven claims only, preventing jargon misuse and ensuring a single source of truth for metrics.
- **[PASS] Principle II (No Silent Fallbacks)**: The plan explicitly defines the failure path if the pipeline fails to generate `outputs/evaluation_report.json` or if JSON schema validation fails. No silent fallbacks are permitted; a failure halts the paper generation process.
- **[PASS] Principle V (Real-Call Testing)**: The plan mandates that the implement-loop testing strategy must use *real* artifacts. Specifically, `reproduce.sh` must be run on a fresh CPU runner to generate real `outputs/` before the Results section is written.
- **[PASS] Principle VI (Convergent Review)**: The plan defines the 'implement↔review loop': implement pipeline -> run 12-panel review -> fix code/paper -> re-verify. The 12-panel review acts as a dynamic gate, not a static check.

### Failure Path & Fallback Strategy
If `infer/run.py` or `eval/run.py` fails to generate the required JSON artifacts:
1. The pipeline halts immediately.
2. No figure generation scripts are executed.
3. The paper generation process is flagged as `blocked_missing_data`.
4. The team must debug the pipeline using `pytest` contract tests before proceeding.
*This prevents the generation of a paper with missing data or mock figures.*

### Real-Call Testing Mandate
Before the "Results" section is drafted:
1. A fresh environment must be spun up (Docker or clean VM).
2. `reproduce.sh` must be executed.
3. The resulting `outputs/evaluation_report.json` must pass schema validation against `contracts/figure-data.schema.yaml`.
4. Only then are figures generated and claims written.

### Convergent Review Loop
1. **Implement**: Code is written and pipeline runs.
2. **Review**: The 12-panel (including this plan) reviews the artifacts.
3. **Fix**: If artifacts fail schema or logic checks, code is fixed.
4. **Re-verify**: The pipeline is re-run, and the loop repeats until all checks pass.

## Paper Structure & Logical Flow

The paper MUST follow this strict logical dependency chain to ensure evidence precedes interpretation:

1. **Abstract**: Summary of the reproduction and key findings (SAA vs. Standard Accuracy).
2. **Introduction**: Contextualize WYSIATI bias and the necessity of SAA.
3. **Methods**: Detail experimental setup, dataset validation, and SAA logic.
4. **Results** (MUST precede Discussion):
 - Present the SAA score and the delta vs. Standard Accuracy (Claim 1).
 - Present the `attribution_hallucination_rate` (Claim 3) derived from `region_only_correct`.
 - Present the `skipped_count` (Claim 2/Data Integrity).
 - *No interpretation of bias implications is allowed here; only raw data presentation.*
5. **Discussion**:
 - Interpret the WYSIATI bias implications based on the Results.
 - Address limitations (e.g., quantization effects vs. general MLLM traits).
6. **References**: Verified bibliography.
7. **Reproducibility Appendix**: Exact commands, seeds, and environment versions.

## Section-by-Section Content Plan

| Section | Content Outline | Dependencies | Length Target |
|:--- |:--- |:--- |:--- |
| **Abstract** | Reproduction success, CPU feasibility, SAA vs. Standard Accuracy delta. | `evaluation_report.json` | 150 words |
| **Introduction** | WYSIATI bias, limitations of standard accuracy, contribution of SAA. | Research Stage Spec | 300 words |
| **Methods** | CPU env, quantization, `validate_dataset.py` logic, SAA formula (IoU=0.5). | `infer/run.py`, `eval/run.py` | 500 words |
| **Results** | **Claim 1**: Delta (Std Acc - SAA). **Claim 2**: Memory usage. **Claim 3**: Hallucination %. | `evaluation_report.json`, `validation_log.json` | 400 words |
| **Discussion** | Implications of bias, quantization limitations, future work. | Results Section | 300 words |
| **Reproducibility** | Seed config, env vars, `reproduce.sh` usage. | `requirements.txt`, `reproduce.sh` | 200 words |

## Claim Defense Strategy

| Claim | Defense Location | Specific Metric/Data Source |
|:--- |:--- |:--- |
| **Claim 1**: "Standard accuracy fails to penalize... leading to overestimation." | Results Section | `standard_accuracy` vs `saa_score` delta from `outputs/evaluation_report.json`. |
| **Claim 2**: "CiteVQA benchmark can be reproduced on free-tier CPU (<7 GB RAM)." | Results Section | `memory_peak_gb` from `outputs/evaluation_report.json`. |
| **Claim 3**: "Roughly [X]% of 'correct' answers are attribution hallucinations." | Results Section | `region_only_correct` / `total_correct_answers` ratio from `outputs/evaluation_report.json`. |

## Required Figures & Generation Plan

### 1. Figure 1: The SAA Calculation Workflow
**Type**: Flowchart / Diagram
**Source**: Logic in `eval/saa_scoring.py` and `eval/metrics.py`.
**Data Binding**: No external data file. Logic diagram.
**Generation Script**: `scripts/plot_workflow.py` (generates TikZ/Mermaid).
**Rationale**: This figure is **necessary** to resolve reader confusion regarding the branching logic of "Answer Correct/Region Wrong" detection, which is too complex to convey clearly via text alone in the Methods section.
**Mandatory Content**:
- Nodes: `Prediction`, `Answer Correct?`, `Region Correct (IoU >= 0.5)?`, `SAA Score`.
- Branches: Explicitly label "Answer Correct/Region Wrong" as **Attribution Hallucination**.
- Legend: Must define SAA, IoU, and Attribution Hallucination without referencing the Methods section.

### 2. Figure 2: Error Distribution Bar Chart
**Type**: Bar Chart
**Source**: `outputs/evaluation_report.json`
**Data Binding**:
```json
{
 "figure_id": "fig_error_distribution",
 "input_file": "outputs/evaluation_report.json",
 "fields": [
 "both_correct",
 "answer_only_correct",
 "region_only_correct",
 "both_wrong"
 ]
}
```
**Generation Script**: `scripts/plot_error_distribution.py` (uses `seaborn.barplot`).
**Mandatory Caption Requirement**: Must explicitly state that the `region_only_correct` bar represents the rate of Attribution Hallucination.

### 3. Figure 3: Dataset Integrity & Skipped Records
**Type**: Stacked Bar Chart (Pie chart rejected for precision)
**Source**: `outputs/validation_log.json`
**Data Binding**:
```json
{
 "figure_id": "fig_data_integrity",
 "input_file": "outputs/validation_log.json",
 "fields": [
 "skipped_reasons"
 ]
}
```
**Generation Script**: `scripts/plot_integrity.py` (uses `matplotlib.bar` stacked).
**Claim Supported**: Demonstrates that data quality issues are negligible (<5%), ensuring they do not skew the SAA metric.
**Mandatory Content**: Must show the `skipped_count` total and the breakdown by reason (e.g., "missing_bbox", "missing_image").

## Project Structure

### Documentation (this feature)

```text
projects/PROJ-601-https-arxiv-org-abs-2605-12882/paper/
├── source/
│ ├── main.tex # Primary LaTeX source
│ ├── figures/ # Auto-generated figures (svg/pdf)
│ └── bib/
│ └── references.bib # Verified bibliography
├── data/
│ ├── validate_dataset.py # Validation logic
│ └──... # Input dataset (submodule)
├── infer/
│ └── run.py # Inference entry point
├── eval/
│ └── run.py # SAA calculation entry point
├── outputs/
│ ├── infer_results.jsonl # Raw predictions
│ ├── evaluation_report.json # Aggregated metrics
│ └── validation_log.json # Skipped records
├── docs/
│ └── reproducibility/
│ └── pipeline_validation.md
├── plan.md # This file
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
 ├── figure-data.schema.yaml
 └── bibliography.schema.yaml
```

### Source Code (repository root)

**Structure Decision**: The project adopts a **Modular Pipeline** structure (Option 1 variant). The `infer/`, `eval/`, and `data/` directories correspond to distinct stages of the research workflow, ensuring separation of concerns as mandated by the reviewer feedback on `citevqa_cpu_adaptation.py`. This structure directly supports the `reproduce.sh` workflow and the generation of specific JSON artifacts required for the paper's figures.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Modular Pipeline** (3 scripts) | Required to generate distinct artifacts (`infer_results.jsonl`, `evaluation_report.json`, `validation_log.json`) for independent verification of each paper claim. | A monolithic script would obscure the data flow, making it impossible to verify the "Data Integrity" (Validation) vs. "Inference" vs. "Evaluation" stages independently as required by FR-003 and FR-005. |
| **JSONL/JSON Artifacts** | Required for machine-readable reproducibility and automated figure generation. | CSV/Text logs are insufficient for the strict schema validation required by the Figure-Generation-Agent and the `evaluation_report.json` schema contract. |

## Discussion Plan: Limitations & Alternative Explanations

The Discussion section MUST explicitly address:
1. **Quantization Artifact vs. General Bias**: Discuss whether the observed attribution hallucination rate is an artifact of the specific quantized model used (Assumption about model behavior) or a general trait of MLLMs. This requires comparing with known full-precision baselines if available, or framing the finding as "under quantized constraints."
2. **CPU Constraints**: Discuss the trade-offs of CPU-only inference (e.g., speed vs. potential non-determinism) as a limitation, not an omission.
3. **IoU Threshold Sensitivity**: Acknowledge that the 0.5 IoU threshold is a community standard but may influence the SAA score, suggesting future sensitivity analysis.