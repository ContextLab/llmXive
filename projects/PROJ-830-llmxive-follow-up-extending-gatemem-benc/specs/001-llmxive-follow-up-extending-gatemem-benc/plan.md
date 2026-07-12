# Implementation Plan: llmXive follow-up: extending "GateMem: Benchmarking Memory Governance in Multi-Principal Shared-Memo"

**Branch**: `001-gatekeeper-governance` | **Date**: 2026-07-12 | **Spec**: `specs/001-llmxive-follow-up-extending-gatemem-benc/spec.md`
**Input**: Feature specification from `specs/001-llmxive-follow-up-extending-gatemem-benc/spec.md`

## Summary

This feature implements a modular governance layer ("Gatekeeper") to benchmark memory access control in LLM agents, addressing the tension between security (preventing unauthorized data leakage) and utility (maintaining task performance). The implementation executes a comparative study against "Retrieval-only" and "Long-Context" baselines using the GateMem dataset. The system will measure three core metrics: **Access Control** (leakage rate), **Conditional Utility** (task success among allowed queries), and **Overall Task Success Rate** (net success including False Positives), alongside **Forgetting** (deletion compliance). Computational costs (latency/RAM) will be profiled on a CPU-only environment. Statistical significance will be determined via Linear Mixed-Effects Models (LMM) with 'Episode ID' and 'Domain' as random intercepts, falling back to paired t-tests/Wilcoxon if multi-domain data is unavailable.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `datasets`, `transformers` (CPU-only), `scikit-learn`, `statsmodels`, `pandas`, `pyyaml`, `pytest`, `huggingface_hub`  
**Storage**: Local filesystem (`data/` for raw/processed data, `data/processed/` for derived artifacts)  
**Testing**: `pytest` (unit tests for pipeline logic, integration tests for full evaluation runs, **contract tests against `contracts/dataset.schema.yaml` and `contracts/results.schema.yaml`**)  
**Target Platform**: Linux (GitHub Actions free-tier runner: a limited CPU count, modest RAM, no GPU. The research question remains to evaluate the feasibility of lightweight CI/CD pipelines under constrained resources. The method involves benchmarking build times and resource utilization across standardized open-source projects (Smith et al.).)  
**Project Type**: Research CLI / Benchmarking Suite  
**Performance Goals**: Must complete full evaluation within 6 hours; peak RAM usage < 7 GB; no GPU acceleration.  
**Constraints**:  
- No CUDA/GPU usage; models must run in default precision on CPU.  
- Dataset must be processed in batches or streamed to fit memory.  
- Statistical analysis must handle potential non-normality via **Wilcoxon signed-rank** or **Kruskal-Wallis** tests if Shapiro-Wilk fails.  
- All random seeds will be fixed to ensure reproducibility.  
**Scale/Scope**: Evaluation of GateMem dataset (medical, office, education, household domains); generation of a representative set of failure case samples for manual review.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Constitution Principle | Compliance Status | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | **COMPLIANT** | All random seeds pinned. `requirements.txt` will pin exact versions. Data fetched from canonical HuggingFace URLs. Scripts runnable end-to-end in isolated venv. |
| **II. Verified Accuracy** | **COMPLIANT** | Citations in `research.md` will strictly use verified URLs from the input block. No invented URLs. |
| **III. Data Hygiene** | **COMPLIANT** | Raw data downloaded to `data/raw/` with checksums recorded. Derivations saved to `data/processed/`. No in-place modification. PII scan enforced via CI. |
| **IV. Single Source of Truth** | **COMPLIANT** | All metrics (Access Control, Conditional Utility, Overall Success, Forgetting) computed by `code/` scripts and traced to `data/processed/` JSON/CSV files. Paper figures generated directly from these files. |
| **V. Versioning Discipline** | **COMPLIANT** | Artifacts (data, code, results) will carry content hashes in `state/` YAML. |
| **VI. Governance-Utility Trade-off Validation** | **COMPLIANT** | Plan explicitly mandates calculation of **Conditional Utility** (success among allowed) and **Overall Success** (net) to decouple gating cost from LLM performance. **Paired statistical tests (LMM with Episode ID random effect, or fallback paired t-test/Wilcoxon)** will compare Gatekeeper vs. Baselines, satisfying the constitution's requirement for paired tests. |
| **VII. Computational Efficiency and Resource Profiling** | **COMPLIANT** | Plan includes instrumentation for wall-clock time and peak RAM usage for both Gatekeeper and Baselines. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-follow-up-extending-gatemem-benc/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    └── results.schema.yaml
```

### Source Code (repository root)

```text
src/
├── gatekeeper/
│   ├── __init__.py
│   ├── pipeline.py          # Main execution logic (Gatekeeper vs. Baselines)
│   ├── classifiers.py       # DistilBERT intent classifier
│   ├── rules.py             # Regex-based rule engine
│   └── metrics.py           # Calculation of Utility, Access Control, Forgetting
├── utils/
│   ├── data_loader.py       # Dataset fetching and parsing (with domain verification)
│   ├── stats.py             # LMM and statistical tests (with fallback logic)
│   └── profiling.py         # CPU/RAM and latency tracking
├── cli/
│   └── run_evaluation.py    # Entry point for the benchmark
└── main.py                  # Orchestrator

tests/
├── contract/
│   ├── test_dataset_schema.py       # Validates against contracts/dataset.schema.yaml
│   └── test_results_schema.py       # Validates against contracts/results.schema.yaml
├── integration/
│   └── test_full_pipeline.py
└── unit/
    ├── test_rules.py
    └── test_metrics.py

data/
├── raw/                     # Downloaded GateMem JSONL files
├── processed/               # Parsed episodes, results
└── samples/                 # failure cases for manual review
```

**Structure Decision**: Single project structure (`src/`) chosen for simplicity and alignment with research CLI nature. Separation of `gatekeeper/`, `utils/`, and `cli/` ensures modularity while keeping the codebase manageable for a single developer/agent. Contracts are explicitly referenced in testing.

## Complexity Tracking

*No violations detected in Constitution Check. Complexity is managed by strict adherence to CPU-only constraints and modular design.*