# Implementation Plan: A Matter of TASTE: Improving Coverage and Difficulty of Agent Benchmarks

**Branch**: `653-taste-benchmark-reproduction` | **Date**: 2024-05-20 | **Spec**: `specs/653-taste-benchmark-reproduction/spec.md`
**Input**: Feature specification from `specs/653-taste-benchmark-reproduction/spec.md`

## Summary

This project reproduces and validates the "A Matter of TASTE" paper by executing its three-stage pipeline (N-gram Modeling, Clustering, Task Synthesis) on the `airline` domain using vendored submodule code. The primary technical approach involves initializing the N-gram model with pre-seeded artifacts, performing CPU-tractable clustering to identify representative medoids, synthesizing tasks, and validating them against domain-specific logic. 

To address scientific soundness concerns, the plan replaces the single heuristic "mock agent" with a **Multi-Heuristic Ensemble** (Regex, Exact Match, and a small CPU-tractable Transformer) to decouple "difficulty" from specific heuristic failure modes. Additionally, a **Proxy Validation Protocol** is introduced to calibrate the ensemble against known LLM failure patterns before the main analysis. The plan strictly adheres to the constraint of running on a free-tier GitHub Actions runner (CPU-only, ~7GB RAM, ≤6h).

## Technical Context

**Language/Version**: Python 3.10 (compatible with GitHub Actions default)  
**Primary Dependencies**: `pyproject.tom` from submodule (likely `numpy`, `scikit-learn`, `pydantic`, `pandas`, `transformers` for CPU-only DistilBERT), `pytest` for testing.  
**Storage**: Local file system (JSON artifacts in `artifacts/`), no external database.  
**Testing**: `pytest` with contract tests against YAML schemas.  
**Target Platform**: Linux (GitHub Actions Runner).  
**Project Type**: CLI/Data Pipeline / Benchmark Reproduction.  
**Performance Goals**: Full pipeline execution ≤ 6 hours; Memory usage < 7 GB.  
**Constraints**: No GPU/CUDA; No external LLM API keys for core pipeline; Must handle missing env vars gracefully (FR-006).  
**Scale/Scope**: Single domain (`airline`) for initial validation; Target ≥ 80% task validity.

## Constitution Check

**Source of Truth**: `projects/PROJ-653-https-arxiv-org-abs-2605-28556/specs/001-https-arxiv-org-abs-2605-28556/constitution.md` (Created as default scientific integrity assumption).

1.  **Reproducibility & Transparency**: The plan explicitly relies on vendored code and pre-seeded artifacts to ensure the pipeline is deterministic and reproducible without hidden external dependencies.
2.  **Computational Feasibility**: The plan strictly excludes GPU-dependent libraries and large-LLM inference, ensuring the project runs within the 2-core/7GB RAM/6h limit of the free CI tier.
3.  **Data Integrity**: Domain validators (`airline.py`) are used to enforce logical coherence, preventing the generation of "hallucinated" or invalid tasks (FR-003).
4.  **Scope Adherence**: The plan addresses every FR and SC in the spec. It does not invent new constraints; it explicitly flags the lack of live LLM evaluation as a limitation addressed via the **Multi-Heuristic Ensemble** and **Proxy Validation Protocol**.
5.  **Error Handling**: The plan incorporates specific steps for mode collapse detection (entropy checks) and retry logic for validation failures, ensuring robustness.
6.  **Scientific Rigor**: The plan implements a **Permutation Test** for statistical significance rather than arbitrary thresholds, and uses **Orthogonal Validation** (Entropy vs. Complexity) to ensure metrics are not tautological.

## Project Structure

### Documentation (this feature)

```text
specs/653-taste-benchmark-reproduction/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── constitution.md      # Default Scientific Integrity Assumption
└── contracts/           # Phase 1 output
    ├── task.schema.yaml
    ├── domain_config.schema.yaml
    └── validation_report.schema.yaml
```

### Source Code (repository root)

```text
# Option 1: Single project (DEFAULT)
src/
├── taste_pipeline/
│   ├── __init__.py
│   ├── stage1_ngram.py       # N-gram initialization & sampling
│   ├── stage2_clustering.py  # Clustering & medoid selection
│   ├── stage3_synthesis.py   # Task generation
│   ├── validators/
│   │   ├── __init__.py
│   │   └── airline.py        # Domain-specific validator
│   └── evaluation/
│       ├── ensemble_agent.py # Multi-Heuristic Ensemble (Regex, Exact, DistilBERT)
│       └── proxy_calibration.py # Proxy Validation Protocol
├── cli/
│   └── main.py               # Entry point (run.sh equivalent)
└── utils/
    ├── entropy.py            # Entropy calculation for mode collapse
    ├── baseline.py           # Synthetic baseline generator
    └── config.py             # Config loading & env var checks

tests/
├── contract/
│   ├── test_task_schema.py
│   └── test_validation_report_schema.py
├── integration/
│   ├── test_pipeline_airline.py
│   └── test_validator_coherence.py
└── unit/
    ├── test_ngram_model.py
    └── test_clustering.py

artifacts/
├── domains/
│   └── airline/
│       ├── tool_spec.json
│       ├── pre_seed.json
│       └── post_seed.json
├── baselines/
│   └── t2_bench_airline.json # Generated or loaded
├── task_sets/
│   └── tasks.json            # Final output
└── reports/
    └── validation_report.json
```

**Structure Decision**: A single-project structure is selected to minimize overhead. The pipeline is modularized into `stage1`, `stage2`, and `stage3` to align with the paper's methodology. The `evaluation` module is isolated to ensure the difficulty evaluation (US-3) can be run independently and robustly.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | No violations detected. The project scope is strictly bounded by the spec and CI constraints. | N/A |

## Phased Implementation Plan

### Phase 0: Research & Environment Setup (Research Complete)
*Goal: Verify dataset/tool availability and finalize the execution strategy.*
- **FR-001, FR-006**: Verify `artifacts/domains/airline/tool_spec.json` and seed files exist. Implement config loader that raises `ConfigurationError` if tools in spec are missing from validators.
- **FR-007**: Analyze `tool_spec.json` to determine max sequence length constraints.
- **SC-003**: Define entropy calculation method (Shannon entropy) for N-gram model output.
- **SC-004**: Profile the N-gram and clustering steps on a sample to ensure they fit within the 6h/7GB RAM limit.
- **US-3 Strategy**: **Proxy Validation Protocol**: Execute a calibration step where the Multi-Heuristic Ensemble is tested against a small set of known LLM failure cases (from literature) to ensure correlation > 0.6 before proceeding.
- **Baseline Strategy**: Verify existence of `τ²-Bench` baseline. If missing, prepare to generate synthetic baseline using `utils/baseline.py`.

### Phase 1: Design & Contracts (Design Complete)
*Goal: Define data schemas and validation rules.*
- **FR-004, FR-005**: Define `Task` and `ValidationReport` schemas in `contracts/`.
- **FR-003**: Formalize the `airline.py` validator logic (input: scenario + sequence; output: valid/invalid + reason).
- **SC-001**: Define the validation report format to track pass/fail rates.
- **SC-002**: Define metrics for "unique tool combinations" calculation.
- **Statistical Rigor**: Define the `ValidationReport` to include p-values from the Permutation Test and Cohen's d effect size.

### Phase 2: Implementation (Implementation Complete)
*Goal: Execute the pipeline and generate artifacts.*
- **FR-001**: Implement `Stage1Ngram`: Load seeds, compute probabilities, sample sequences. Add entropy check to detect mode collapse (Edge Case 1).
- **FR-002**: Implement `Stage2Clustering`: Cluster sampled sequences, select ≥5 medoids.
- **2.3 Task Generation (FR-004)**: Generate natural language scenarios for medoids. Populate `Task.scenario` and `Task.action_sequence`.
- **2.4 Validation Integration (FR-003)**: Integrate `airline.py` validator. Update `Task.validation_status` and `Task.validation_reason`. Loop until ≥80% validity (SC-001) or max retries.
- **2.5 Baseline Handling**: If `τ²-Bench` is missing, execute `utils/baseline.py` to generate a synthetic baseline (randomized sequences with preserved length distribution) to ensure comparability.
- **2.6 Difficulty Evaluation**: Execute `evaluation/ensemble_agent.py` on both TASTE and Baseline sets. Calculate the **Heuristic Complexity Gap** (difference in consensus failure rates).
- **2.7 Statistical Analysis**: Run Permutation Test on the gap. Calculate Cohen's d.

### Phase 3: Validation & Testing (Research Complete)
*Goal: Verify all Success Criteria and Edge Cases.*
- **SC-001**: Run integration tests to confirm ≥80% validation rate for `airline`.
- **SC-002**: Calculate tool combination diversity; verify ≥2.0x increase over baseline.
- **SC-003**: Verify N-gram entropy > 0.5.
- **SC-004**: Measure total runtime; ensure ≤6 hours.
- **SC-005**: Verify **Statistical Significance (p < 0.05)** and **Effect Size (Cohen's d > 0.5)** for the difficulty drop.
- **Edge Cases**:
    - Test mode collapse detection (entropy check triggers re-sampling).
    - Test `ConfigurationError` when `tool_spec.json` references unknown tools.
    - Test retry logic for validation failures (with a limited number of attempts).
    - Test Proxy Validation Protocol (correlation check).

### Phase 4: Documentation & Reporting (Documentation Complete)
*Goal: Finalize `research.md`, `data-model.md`, and `quickstart.md`.*
- Update `research.md` with final dataset verification and methodology rationale.
- Update `quickstart.md` with exact commands to reproduce the `airline` domain results.
- Ensure all `contracts/*.schema.yaml` files are valid and referenced in tests.
