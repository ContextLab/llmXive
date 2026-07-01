# Implementation Plan: Evaluating the Impact of LLM-Generated Code on Memory Usage

**Branch**: `001-eval-llm-memory-impact` | **Date**: 2024-01-15 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-eval-llm-memory-impact/spec.md`

## Summary

This plan implements a computational pipeline to evaluate whether LLM‑generated code exhibits systematically different memory consumption patterns compared to human‑written code. The system selects **HumanEval** as the **exclusive** benchmark dataset (it provides executable human reference solutions), generates solutions using a CPU‑tractable model (Phi‑3‑mini‑3.8B), profiles memory usage via `tracemalloc` and `memory_profiler`, and performs rigorous statistical analysis.

Key methodological choices:

1. **Dataset**: HumanEval (`openai/humaneval`) – the only dataset that satisfies the paired‑design requirement.
2. **Model**: Phi‑3‑mini‑3.8B (or fallback TinyLlama‑1.1B) in CPU‑only mode, generation timeout 180 s.
3. **Primary Metric**: **Efficiency Score** = `peak_memory_bytes * execution_time_seconds` for *successful* runs.
4. **Secondary Metrics**: Failure‑rate comparison, descriptive Total Resource Cost, regression of raw `peak_memory_bytes` on static code features.
5. **Statistical Tests**:
   - Permutation test (10 000 iterations) on paired Efficiency Score differences.
   - Holm‑Bonferroni correction when ≥3 hypothesis tests are performed.
   - Chi‑square (or Fisher’s Exact) test for failure‑rate differences.
   - Linear regression with VIF diagnostics for code‑feature analysis.

All steps are ordered so that data download precedes generation, generation precedes profiling, profiling precedes feature extraction, and analysis follows profiling.

## Constitution Check

| Principle | Compliance Strategy | Status |
|-----------|---------------------|--------|
| **I. Reproducibility** | Random seeds pinned in `code/config.yaml`; immutable HF dataset revision recorded; `requirements.txt` pins versions. | ✅ Pass |
| **II. Verified Accuracy** | HumanEval is a verified HF dataset with a public URL; no unverified sources used. | ✅ Pass |
| **III. Data Hygiene** | Raw dataset stored under `data/raw/` with SHA‑256 checksum; all transformations write new files under `data/processed/`. | ✅ Pass |
| **IV. Single Source of Truth** | All figures and statistics trace back to rows in `data/processed/results.csv` and `data/processed/statistical_results.json` (schema defined in `data-model.md`). | ✅ Pass |
| **V. Versioning Discipline** | Content hashes recorded in `state/...yaml`; any change updates `artifact_hashes`. | ✅ Pass |
| **VI. Controlled Profiling Environment** | `code/profiling_env.yaml` records OS, Python, and library versions; runs in isolated virtualenv. | ✅ Pass |
| **VII. Benchmark Dataset Versioning** | Exact HF identifier and revision stored in `data/dataset_manifest.yaml` (see `data-model.md`). Raw HumanEval data never modified. | ✅ Pass |

## Technical Context

- **Dataset Choice**: HumanEval exclusively (verified, provides human reference solutions and deterministic test inputs). MBPP is excluded because it lacks executable human baselines for the required paired design.
- **Model Choice**: Phi‑3‑mini‑3.8B (CPU‑only). If OOM occurs, fallback to TinyLlama‑1.1B.
- **Runtime Budget**: Target **N = 30** paired problems.
  - Generation: ≤180 s per problem → ≤1.5 h total.
  - Profiling: ≤60 s per solution (2 solutions per problem) → ≤1 h total.
  - Feature extraction & analysis: ≤30 min.
  - Overheads (data I/O, model loading, logging): ≤30 min.
  - **Total ≈ 3.5 h**, well under the 6 h CI limit with ample buffer.
- **Compute Constraints**: No GPU, no 8‑bit/4‑bit quantization, all libraries CPU‑compatible.

## Project Structure

### Documentation (this feature)

```text
specs/001-eval-llm-memory-impact/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── code_feature.schema.yaml
│   ├── memory_measurement.schema.yaml
│   └── statistical_result.schema.yaml
└── tasks.md
```

### Source Code (repository root)

```text
projects/PROJ-395-evaluating-the-impact-of-llm-generated-c/
├── code/
│   ├── __init__.py
│   ├── config.yaml               # seeds, dataset choice, timeouts, num_problems=30
│   ├── profiling_env.yaml        # environment snapshot
│   ├── download_data.py          # FR‑001
│   ├── generate_llm.py           # FR‑002
│   ├── profile_memory.py         # FR‑003, FR‑010, FR‑011
│   ├── extract_features.py       # FR‑006
│   ├── analyze_stats.py          # FR‑004, FR‑005, FR‑013, regression, VIF
│   └── utils.py                  # helpers, VIF, error handling
├── data/
│   ├── raw/
│   ├── processed/
│   └── dataset_manifest.yaml     # dataset versioning record (see data-model.md)
├── tests/
│   ├── unit/
│   └── integration/
├── requirements.txt
└── README.md
```

**Rationale for Single‑Project Layout**: Simplicity, minimal overhead, and clear traceability between code, data, and results, satisfying the Constitution’s Single Source of Truth principle.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| N/A | All constitutional principles satisfied with standard practices. | N/A |
