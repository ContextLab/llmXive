# Implementation Plan: llmXive follow-up: extending "SWE-Explore: Benchmarking How Coding Agents Explore Repositories"

**Branch**: `001-iterative-exploration-benchmark` | **Date**: 2026-07-14 | **Spec**: `specs/001-iterative-exploration-benchmark/spec.md`
**Input**: Feature specification from `/specs/001-iterative-exploration-benchmark/spec.md`

## Summary

This project implements a comparative study to determine if an iterative, feedback-driven exploration strategy yields higher line-level coverage and ranking efficiency compared to the static, one-shot exploration baseline on the "hard" (bottom coverage tier) and synthetic ambiguous subsets of the SWE-Explore dataset. The implementation prioritizes CPU-feasibility by utilizing quantized models (Qwen/LLaMA) for the agent loop, strict static analysis (AST/pylint) + **sandboxed execution** for feedback signals, and non-parametric statistical testing (Wilcoxon signed-rank with Bonferroni correction and tie-handling) for results.

Key updates in this revision:
1.  **Turn Limit Sweep**: The iterative agent now logs results for multiple turn counts simultaneously to measure sensitivity (SC-006).
2.  **Structural Obfuscation**: Explicitly defined as a mandatory step in data curation (FR-009).
3.  **Validation Report**: A `validation_report.md` is generated to satisfy FR-010.
4.  **Feasibility Timer**: Runtime is measured and logged to verify the temporal constraint. (SC-005).
5.  **Tie-Handling**: Explicit fallback to permutation test if >50% ties (FR-006).
6.  **Line Mapping**: Synthetic issues use token-based line remapping for ground truth validity.

## Technical Context

**Language/Version**: Python 3.x  
**Primary Dependencies**: `datasets` (Hugging Face), `transformers` (with `bitsandbytes` for -bit quantization), `scipy` (statistical tests), `pylint` (static analysis), `ast` (stdlib), `pandas`, `numpy`, `jsonschema` (for contract validation).  
**Storage**: Local filesystem (`data/` for raw/curated datasets, `data/results/` for logs/metrics). No external database.  
**Testing**: `pytest` for unit tests on mutation logic and metric calculation; **integration tests validate log outputs against `contracts/*.yaml` schemas** (using `jsonschema`).  
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, ~7GB RAM).  
**Project Type**: Research CLI / Data Analysis Pipeline.  
**Performance Goals**: Complete full pipeline (download -> curate -> run baseline -> run iterative -> stats) within 6 hours on CPU. **Runtime is measured and logged to `data/results/metrics.csv`**.  
**Constraints**: Max few turns per issue; Low-bit quantization required for LLM to fit in constrained RAM; no GPU dependency for the primary run (GPU offload only if 8-bit CPU fails or for specific validation steps).  
**Scale/Scope**: [deferred] of SWE-Explore dataset (A moderate number of issues) + A set of synthetic issues.

> **Dataset Note**: The plan relies on the verified SWE-Explore dataset (jsonl). If the native `initial_coverage_score` is missing, a **local AST-based retrieval simulation** is performed to derive the metric, ensuring dataset fit. No access-gated data is used.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Evidence / Action Required |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates pinned seeds (`numpy`, `torch`), `requirements.txt` in `code/`, and CI-based execution. All data fetched via programmatic Hugging Face loaders. |
| **II. Verified Accuracy** | **PASS** | Citations limited to verified URLs (SWE-Explore HF link) as listed in `research.md`. No external claims without source. |
| **III. Data Hygiene** | **PASS** | Raw data preserved in `data/raw/`. Curated "hard" and "synthetic" subsets written to `data/curated/` with new filenames and checksums. No in-place modification. |
| **IV. Single Source of Truth** | **PASS** | All metrics derived from `data/results/metrics.csv` (structure defined in `data-model.md`). Paper figures generated directly from this file. No manual entry. |
| **V. Versioning Discipline** | **PASS** | Content hashes tracked in `state/`. `requirements.txt` pins versions. |
| **VI. Iterative Feedback Validation** | **PASS** | Plan mandates logging of `query_history` and `static_analysis_signals` in `data/results/iterative_logs.jsonl` for every turn. Schema defined in `contracts/agent_log_schema.yaml`. |
| **VII. Hard-Tail Dataset Integrity** | **PASS** | "Hard" subset (lowest-performing tier) and synthetic set (50 issues) defined as immutable artifacts in `data/curated/`. **Runtime checksum verification** is performed before loading to ensure integrity. |

## Project Structure

### Documentation (this feature)

```text
specs/001-iterative-exploration-benchmark/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (Static definitions, NOT in code/)
│   ├── dataset_schema.yaml
│   ├── agent_log_schema.yaml
│   └── result_schema.yaml
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
projects/PROJ-897-llmxive-follow-up-extending-swe-explore/
├── code/
│   ├── __init__.py
│   ├── config.py                # Global config, seeds, paths
│   ├── data/
│   │   ├── download.py          # Download SWE-Explore, verify checksum
│   │   ├── curate.py            # Filter "hard", generate synthetic ambiguous, validate, checksum
│   │   └── utils.py             # Data loading helpers (streaming)
│   ├── agent/
│   │   ├── base.py              # Abstract agent interfaces
│   │   ├── static_baseline.py   # One-shot retrieval agent (INDEPENDENT EXECUTION)
│   │   ├── iterative.py         # Multi-turn agent with feedback loop + Loop Detection
│   │   ├── quantized_llm.py     # 8-bit LLM wrapper (CPU-optimized)
│   │   └── static_analysis.py   # Pylint/AST/Sandbox error extraction
│   ├── metrics/
│   │   ├── coverage.py          # Line-level coverage calculation (with token mapping)
│   │   ├── ranking.py           # Ranking efficiency calculation
│   │   └── stats.py             # Wilcoxon/Permutation tests (with tie-handling)
│   └── main.py                  # Orchestration script (with Runtime Timer)
├── data/
│   ├── raw/                     # Downloaded SWE-Explore (immutable)
│   ├── curated/                 # Hard subset, Synthetic subset (checksummed)
│   └── results/                 # Logs, metrics, stats outputs
├── tests/
│   ├── unit/
│   │   ├── test_mutations.py    # Validate synthetic generation
│   │   └── test_metrics.py      # Validate coverage/ranking logic
│   └── integration/
│       └── test_agent_loop.py   # End-to-end -turn loop test (validates against contracts/)
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure selected to minimize overhead for a research pipeline. `code/` is modularized by domain (data, agent, metrics) to ensure separation of concerns and testability. `data/` is strictly read-only for raw inputs and append-only for results. **`contracts/` are static definitions in `specs/`, not part of `code/`**.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Iterative Agent Loop** | Required by US-2 to test feedback-driven strategy. | A static baseline alone cannot answer the research question regarding "iterative" benefits. |
| **8-bit Quantization** | Required to run LLM on CPU within 7GB RAM (SC-005). | Full precision models exceed memory; CPU-only inference of full models is too slow for the practical time limit. |
| **Synthetic Mutation** | Required by US-1 to create "ambiguous" ground truth where none exists. | Using only "hard" real issues is insufficient; we need a controlled ambiguity variable. |
| **Statistical Rigor** | Required by FR-006/SC-004 (Wilcoxon + Bonferroni + Tie-Handling). | Simple mean comparison ignores distribution shape and multiple testing risks. **See FR-006 and data-model.md Statistical Result section**. |
| **Turn Limit Sweep** | Required by SC-006 to measure sensitivity. | Fixed 3-turn limit risks Type II error if optimal turns > 3. |
| **Structural Obfuscation** | Required by FR-009 to ensure synthetic issues are actually harder. | Variable renaming alone is insufficient for robustness testing. |

## Task Ordering & Dependencies

- **Phase 0 (Research)**: `research.md` generation.
- **Phase 1 (Data & Contracts)**: `curate.py` (with checksum validation), `contracts/*.yaml`.
- **Phase 2 (Foundation)**: `quantized_llm.py`, `static_analysis.py`, `download.py`.
- **Phase 3 (Baseline)**: `static_baseline.py` (INDEPENDENT execution).
- **Phase 4 (Iterative)**: `iterative.py` (with Loop Detection & Early Exit).
- **Phase 5 (Metrics & Stats)**: `coverage.py`, `ranking.py`, `stats.py` (with tie-handling).
- **Phase 6 (Validation)**: `validation_report.md` generation.

**Note**: `T047` (Loop Detection) is implemented in Phase 4 as part of the core iterative agent loop, not delayed.

## Data Availability & Feasibility

- **SWE-Explore**: Downloaded via `datasets.load_dataset("SWE-Explore-Bench/SWE-Explore-Bench")`.
- **Hard Instance Proxy**: If `initial_coverage_score` is missing, a local AST-based retrieval simulation is run to compute a proxy score. **No external mismatched datasets are used.**
- **Streaming**: Full dataset loaded via streaming; only curated subsets materialized.
- **Compute**: Reduced-precision quantization ensures CPU feasibility. If 8-bit CPU fails, the execution stage offloads to Kaggle GPU (scaled down).
