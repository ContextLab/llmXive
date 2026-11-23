# Implementation Plan: Episodic Future Thinking in LLMs

**Branch**: `001-episodic-future-thinking` | **Date**: 2026-06-01 | **Spec**: `specs/001-episodic-future-thinking/spec.md`
**Input**: Feature specification from `/specs/001-episodic-future-thinking/spec.md`

## Summary

This project implements a neural episodic control module augmented to a standard transformer architecture to enable "mental time travel" (simulating future scenarios based on past episodic memories). The core technical approach involves storing (state, action, outcome) tuples from ALFWorld/TextWorld environments in a CPU-optimized vector index (HNSW/FAISS), retrieving relevant episodes via cosine similarity (threshold 0.75), and injecting these retrieved embeddings into the transformer's attention mechanism during planning inference. The implementation strictly adheres to CPU-only constraints (7GB RAM, 14GB disk) and validates the architecture against a baseline transformer using mixed-effects modeling on held-out tasks, with specific validation protocols for counterfactual confidence and retrieval sensitivity. Crucially, the design includes a **Zero-Shot Episodic Control** (testing on disjoint state manifolds) and **Ablation Studies** to distinguish true episodic retrieval from statistical memorization, addressing causal identification concerns.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `torch` (CPU-only), `faiss-cpu`, `datasets`, `scikit-learn`, `statsmodels`, `pandas`, `pyyaml`, `numpy`
**Storage**: Local filesystem (`data/`), FAISS index files (`.index`)
**Testing**: `pytest` (unit/integration), `pytest-cov`
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, 7GB RAM)
**Project Type**: Research Library / Benchmarking Suite
**Performance Goals**: Retrieval latency ≤ 500ms on CPU (T018); Model inference < 6h per job; Memory footprint < 7GB (T017)
**Constraints**: No GPU usage for training/inference; No external API calls for data; Fixed cosine threshold 0.75 for operational retrieval (T009); Sensitivity sweep {0.70, 0.75, 0.80} (T029); Mixed-effects modeling or permutation tests (T021); ≥1 episodic reference per plan (T020).
**Scale/Scope**: [deferred] stored episodes; + held-out planning tasks; similarity thresholds.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Action / Note |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All seeds pinned in `code/config.yaml`; ALFWorld/TextWorld fetched from verified HuggingFace URLs with commit hashes recorded; `requirements.txt` pins versions. |
| **II. Verified Accuracy** | **PASS** | Citations in `research.md` and `plan.md` will be validated against primary sources (Pritzel et al.,; ALFWorld repo) before acceptance. Reference-Validator Agent will run with `CITATION_TITLE_OVERLAP_THRESHOLD` check on these artifacts. |
| **III. Data Hygiene** | **PASS** | `data/` directory will store checksums; raw data immutable; derivations in `data/processed/`; PII scan enforced. |
| **IV. Single Source of Truth** | **PASS** | All results trace to `data/` rows and `code/` blocks; no hand-typed stats in `paper/`. |
| **V. Versioning Discipline** | **PASS** | Task T001 explicitly calculates content hashes and updates the `state/` file upon artifact change. |
| **VI. Computational Budget** | **PASS** | M param model target; FAISS HNSW for CPU efficiency; memory profiling in CI (T017); quantized embeddings used to ensure 7GB compliance. |
| **VII. Statistical Power** | **PASS** | Power analysis (n=10 task variants, d=0.8, α=0.05) implemented; underpowered results flagged explicitly. **Pilot Study** (n=5 tasks) conducted to empirically estimate variance components before final analysis. |

## Project Structure

### Documentation (this feature)

```text
specs/001-episodic-future-thinking/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── episodic_memory.schema.yaml
│   ├── planning_task.schema.yaml
│   ├── evaluation_result.schema.yaml
│   └── future_scenario.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-587-episodic-future-thinking-in-llms-impleme/code/
├── config.yaml          # Created by T009 (log levels, thresholds)
├── data/
│   ├── raw/             # Downloaded datasets (checksummed)
│   └── processed/       # Trajectories, embeddings, indices
├── src/
│   ├── episodic_memory/
│   │   ├── __init__.py
│   │   ├── store.py     # FAISS HNSW implementation
│   │   └── retrieval.py # Cosine similarity search
│   ├── models/
│   │   ├── __init__.py
│   │   ├── baseline.py  # Standard Transformer
│   │   └── episodic.py  # Augmented Transformer
│   ├── planning/
│   │   ├── __init__.py
│   │   ├── generator.py # Plan generation logic
│   │   └── constraints.py # Enforce ≥1 episodic reference
│   ├── evaluation/
│   │   ├── __init__.py
│   │   ├── accuracy.py  # Mixed-effects modeling
│   │   ├── confidence.py # Counterfactual validation
│   │   └── sensitivity.py # Threshold sweep {0.70, 0.75, 0.80}
│   └── utils/
│       ├── power.py     # Power analysis implementation
│       └── loaders.py   # Dataset fetching
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
└── requirements.txt
```

**Structure Decision**: Single project structure under `code/` is selected to minimize I/O overhead on the CI runner and align with the "Research Library" scope. The `src/` directory is modularized to separate the episodic memory mechanism from the planning logic, ensuring the `constraints.py` module can explicitly enforce the "≥1 episodic reference" requirement (FR-003) during generation, addressed by Task T020.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Episodic Memory Module** | Required to distinguish true episodic recollection from semantic pattern completion (US-3). | A simple RAG (Retrieval-Augmented Generation) without explicit (state, action, outcome) tuple storage and temporal indexing fails to model the "mental time travel" mechanism and cannot support the counterfactual validation protocol. |
| **Mixed-Effects Modeling** | Required to handle task-level variance and repeated measures across 50+ tasks (FR-004). | Simple t-tests would ignore the hierarchical structure of the data (tasks nested within environments), inflating Type I error rates and violating the statistical rigor requirement. |
| **FAISS HNSW Index** | Required to achieve ≤500ms retrieval latency on CPU with ≥10k entries (FR-001). | Linear scan (brute force) would exceed the 500ms latency budget as the memory store grows, violating the performance constraint. |
| **Permutation Tests** | Required as a fallback if normality assumptions fail (FR-004). | Mixed-effects modeling alone is invalid if data is non-normal; permutation tests provide a robust non-parametric alternative. |
| **Forward Simulation** | Required to operationalize "simulation" rather than just recall (Scientific Soundness). | Simple concatenation of embeddings does not enable prediction of future states; a learned transition model is needed to distinguish "mental time travel" from standard RAG. |

## Methodology & Experimental Design

### 4.1 Architecture Design
- **Baseline**: A 70M parameter Transformer (CPU-optimized) trained on the benchmark tasks.
- **Episodic Model**: The baseline architecture augmented with a Neural Episodic Control (NEC) module.
  - **Memory Store**: FAISS HNSW index storing embeddings of (state, action, outcome) tuples.
  - **Retrieval**: Cosine similarity search with a fixed operational threshold of 0.75 (FR-002, T009).
  - **Integration**: Retrieved episode embeddings are concatenated with the current state embedding before the attention layers.
  - **Forward Simulation**: The model uses retrieved past states to predict the *next* state via a learned transition model, explicitly operationalizing "simulation" rather than just recall. This addresses the concern that concatenation alone does not enable planning.

### 4.2 Causal Identification & Ablation
- **Zero-Shot Episodic Control**: To distinguish retrieval efficacy from statistical memorization, the model will be tested on a **disjoint state manifold** (TextWorld tasks) where the training data (ALFWorld) provides no semantic overlap. Success on these tasks will be attributed to the retrieval mechanism, not memorization.
- **Ablation**: The memory module will be ablated (replaced with random noise) to confirm performance degradation is due to the memory mechanism, not just increased parameter count.
- **Conditional Analysis**: The primary analysis will model success *conditional* on retrieval precision (SC-002). Retrieval precision is validated first (T022), then included as a covariate in the mixed-effects model to avoid conflating module existence with retrieval quality.

### 4.3 Statistical Analysis Plan
- **Primary Test**: Mixed-effects modeling (lme4-style) with `task_id` as a random effect to account for task difficulty variance.
  - **Model**: `Accuracy ~ Condition + Retrieval_Precision + (1|task_id)`
  - **Correction**: Bonferroni correction applied if ≥10 task variants are tested (FR-008, T023).
  - **Fallback**: Permutation tests if Shapiro-Wilk test p-value < 0.05 (FR-004, T021).
- **Power Analysis**: Pre-registered target of n=10 task *variants* (random effect groups), α=0.05, power=0.80, detectable effect size d=0.8. A **Pilot Study** (n=5 tasks) will be conducted first to empirically estimate variance components before finalizing the power analysis, resolving circularity concerns.
- **Sensitivity Analysis**: Explicit sweep of similarity thresholds ∈ {0.70, 0.75, 0.80} to verify robustness (FR-006, T029).

### 4.4 Counterfactual Generation Protocol
- **Method**: Counterfactual details are generated by swapping outcome values from *unrelated* stored episodes (not random noise) to create "known-unknowns".
- **Verification**: The ground truth of these perturbed details is verified against the original source episodes to ensure the "known-unknown" status is accurate. This ensures construct validity for confidence calibration (FR-005, T027b).

### 4.5 Human Evaluation Protocol
- **Execution**: For the final paper and SC-004, a **Human Evaluation** phase is defined (T027a). This involves recruiting ≥3 raters, collecting Likert scale ratings for scenario coherence, and calculating inter-rater reliability. This replaces "simulated" ratings to satisfy the requirement for human evaluation.

## Phases & Tasks (Summary)

- **Phase 0: Pre-Analysis & Setup**
  - T001: Versioning & Hashing (Calculate content hashes, update `state/` upon artifact change)
  - T009: Config Creation (Create `config.yaml` with log levels and **validate fixed threshold 0.75**)
  - T013: Pilot Study (n=5 tasks to estimate variance components for power analysis)
- **Phase 1: Data Ingestion & Indexing**
  - T004a: Data Download (Fetch ALFWorld/TextWorld datasets from verified sources)
  - T011b: Trajectory Extraction (Generate `trajectories.parquet`)
  - T012: Episodic Memory Store (Build FAISS HNSW index)
- **Phase 2: Model Implementation**
  - T019b: Power Analysis Implementation (Implement `run_power_analysis()` with pilot data)
  - T020: Planning Service (Implement generation with **assertion of ≥1 episodic reference**)
  - T021: Permutation Test Fallback (Implement if Shapiro-Wilk p < 0.05)
- **Phase 3: Evaluation & Validation**
  - T017: Resource Profiling (**Verify RAM/disk constraints** < 7GB/14GB)
  - T018: Latency Benchmark (**Measure retrieval latency** ≤ 500ms)
  - T022: Retrieval Precision Test (**Generate ground-truth labels**, measure precision for SC-002/US-1)
  - T023: Mixed-Effects Test (Run main analysis, **apply Bonferroni correction** if needed)
  - T027a: Human Evaluation Protocol (**Recruit raters**, collect ratings, calculate reliability for SC-004)
  - T027b: Counterfactual Generation (**Generate perturbed scenarios** via controlled perturbation for FR-005/US-3)
  - T027c: Validation Service (Calculate inter-rater reliability, **measure confidence calibration** against verifiable truth for SC-003)
  - T029: Sensitivity Sweep (**Execute sweep** {0.70, 0.75, 0.80} and report precision variation for SC-005)
  - T024: Zero-Shot Control (Test on disjoint TextWorld tasks to validate causal mechanism)

## Compute Feasibility

- **CPU-First Strategy**: All training and inference will run on CPU using `faiss-cpu` and `torch` (CPU build).
- **Memory Management**:
  - Dataset streaming (`datasets.load_dataset(..., streaming=True)`) to avoid loading full datasets into RAM.
  - FAISS index built incrementally to stay within 7GB RAM.
  - **Quantized Embeddings**: Use an -bit quantized embedding model and batched processing to ensure the 7GB RAM constraint is met with the cited datasets, addressing the memory feasibility concern.
- **No GPU Fabrication**: No synthetic CPU approximations of GPU tasks. If a specific operation requires GPU (e.g., large-scale embedding generation), it will be scaled down to a representative subset or offloaded to the Kaggle GPU escape hatch if the code explicitly detects CUDA requirements (though the plan prioritizes CPU-only execution).
