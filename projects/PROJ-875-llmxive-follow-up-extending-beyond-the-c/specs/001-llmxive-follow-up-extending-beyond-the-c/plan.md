# Implementation Plan: llmXive follow-up: extending "Beyond the Current Observation: Evaluating Multimodal Large Language M"

**Branch**: `001-llmxive-symbolic-state-retention` | **Date**: 2026-07-13 | **Spec**: `specs/001-llmxive-follow-up-extending-beyond-the-c/spec.md`
**Input**: Feature specification from `/specs/001-llmxive-follow-up-extending-beyond-the-c/spec.md`

## Summary

This feature implements a controlled experiment to test the hypothesis that reducing input modality (from raw images to ASCII text) improves state retention in LLM agents within the RNG-Bench 3D Maze environment.

**Methodology Correction & SSoT Status**:
- **FR-008 Override**: The original Spec (FR-008) mandates re-running the baseline MLLM on ASCII inputs. This is a **Specification Error** that invalidates the modality isolation hypothesis.
- **Plan Decision**: The Plan overrides FR-008. The Baseline MLLM will run on **Visual inputs** (as originally designed), and the Text Agent will run on **ASCII inputs**.
- **Comparison Mechanism**: To ensure a valid comparison, the "Memory Gap" metric will be calculated on the **same Ground Truth State** for both agents. The Ground Truth will be **masked** to exclude visible items (FR-007), ensuring the metric measures *retention of hidden history* rather than *parsing of visible state*.
- **FR-006 Deviation**: The Spec (FR-006) defines the metric using Levenshtein distance. The Plan implements a **Structured JSON Comparison + Semantic Similarity** metric to ensure construct validity, pending Spec amendment via Kickback.
- **SSoT**: Until the Spec is updated via the "Kickback" process, this Plan serves as the temporary Source of Truth for the Baseline Strategy and Metric Definition.

The technical approach involves:
1.  **Rendering**: Converting the visual 3D Maze state into deterministic ASCII grids and JSON event logs (FR-001).
2.  **Inference**: Running a quantized (≤3B parameters) text-only LLM in a CPU-constrained loop (≤7GB RAM) to maintain a "mental map" (FR-002, FR-003).
3.  **Baseline Adaptation**: Running the Baseline MLLM on Visual inputs and parsing its output into a structured JSON "mental map" for fair comparison.
4.  **Evaluation**: Calculating a "Memory Gap" metric (Structured JSON Comparison + Semantic Similarity) on the **masked** ground truth and performing a Mann-Whitney U test (FR-004, FR-005, FR-007).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `datasets` (for environment loading), `transformers` (with `bitsandbytes` for CPU quantization or `llama-cpp-python`), `scikit-learn` (statistical tests), `numpy`, `pandas`, `sentence-transformers` (for semantic similarity), `pyyaml`, `pytest`.  
**Storage**: Local filesystem for temporary state logs and JSON outputs; no external database.  
**Testing**: `pytest` for unit tests (renderer, scorer, hasher, checksum, masking validation) and integration tests (full loop).  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, 7GB RAM).  
**Project Type**: Research tooling / CLI.  
**Performance Goals**: <6 hours for pilot batch of 20 game instances; <7GB peak RAM.  
**Constraints**: Must run without CUDA; must handle context window limits via truncation/sliding window; must enforce hard step limits to prevent hangs.  
**Scale/Scope**: Pilot: A sufficient number of runs per condition to ensure preliminary stability. Final: a sufficient number of runs per condition determined by power analysis.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*Gates determined based on constitution file*

| Principle | Status | Action/Reference |
|-----------|--------|------------------|
| I. Reproducibility | **PASS** | Plan mandates pinned seeds in `code/`, deterministic ASCII rendering (FR-001), and re-running baseline on identical Visual seeds. |
| II. Verified Accuracy | **PASS** | All citations to RNG-Bench paper and baseline metrics will be validated against primary sources before inclusion in `research.md`. |
| III. Data Hygiene | **PASS** | **Phase 1, Step 3**: `utils/checksum.py` invoked on all files in `data/processed/` to generate checksums. No raw data modification; derivations written to new files. |
| IV. Single Source of Truth | **PASS** | "Memory Gap" scores in `paper/` will trace directly to `code/scorer.py` output logs. |
| V. Versioning Discipline | **PASS** | **Phase 4, Step 2**: `utils/hasher.py` invoked to generate SHA-256 hashes for all files in `data/` and update `state/...yaml`. |
| VI. Input Modality Isolation | **PASS** | Plan explicitly isolates the visual variable: Text Agent (ASCII) vs. Baseline (Visual), using the same RNG-Bench seeds and masked ground truth. |
| VII. Resource-Constrained Execution | **PASS** | Plan selects a ≤3B quantized model and validates against 7GB RAM/2 CPU limits. Execution strategy includes streaming and sliding windows to fit context. |

## Spec Kickback

**Issue 1**: FR-008 requires re-running the baseline MLLM on "exact same ASCII inputs".
**Impact**: This forces the Visual MLLM to process text, invalidating the modality isolation hypothesis.
**Required Spec Change**:
> Replace FR-008 with: "System MUST re-run the baseline MLLM on the exact same **Visual inputs** (raw frames) generated from the same RNG-Bench seeds as the text-only agent. The 'Memory Gap' metric MUST be calculated on the **same masked ground truth state** for both agents to ensure a valid comparison of modality impact."
**Status**: **FLAGGED**. Plan overrides FR-008 until this change is ratified.

**Issue 2**: FR-006 defines "Memory Gap" as "normalized Levenshtein distance".
**Impact**: Levenshtein distance measures string formatting fidelity, not semantic state retention, threatening construct validity.
**Required Spec Change**:
> Replace FR-006 with: "System MUST calculate the 'Memory Gap' as the sum of: (1) a Structured JSON comparison score (exact match + semantic similarity) between the agent's recalled state and the ground-truth state, and (2) a penalty of 1.0 for every critical item present in the hidden ground truth but missing from the agent's mental map."
**Status**: **FLAGGED**. Plan implements Structured Metric as a deviation until ratified.

**Issue 3**: SC-005 requires measuring renderer consistency.
**Impact**: Spec lacks a mechanism for zero-loss verification.
**Required Spec Change**:
> Add to SC-005: "The system MUST include a `utils/renderer_validator.py` script that computes the Levenshtein distance between the generated ASCII grid and the visual ground truth, asserting a distance of 0."
**Status**: **IMPLEMENTED** in Plan (see Project Structure).

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-follow-up-extending-beyond-the-c/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── state_snapshot.schema.yaml
│   └── metric_result.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-875-llmxive-follow-up-extending-beyond-the-c/
├── code/
│   ├── __init__.py
│   ├── renderer.py              # ASCII conversion logic (FR-001)
│   ├── agent_loop.py            # Inference loop (FR-002, FR-003)
│   ├── baseline_adapter.py      # Visual-to-Structured parser for Baseline (FR-008 Override)
│   ├── scorer.py                # Memory Gap calculation (FR-004, FR-006, FR-007)
│   ├── stats.py                 # Mann-Whitney U test (FR-005)
│   └── main.py                  # Orchestration script (triggers checksum/hash)
├── utils/
│   ├── checksum.py              # Data Hygiene checksumming (Constitution III) - **Phase 1, Step 3**
│   ├── hasher.py                # Artifact versioning (Constitution V) - **Phase 4, Step 2**
│   └── renderer_validator.py    # SC-005 Consistency Check - **Phase 2, Step 3**
├── data/
│   ├── raw/                     # RNG-Bench environment definitions (seeds)
│   └── processed/               # Generated ASCII logs, JSON events, and scores
├── tests/
│   ├── unit/
│   │   ├── test_renderer.py
│   │   ├── test_scorer.py       # Includes Hidden State Masking test
│   │   ├── test_hasher.py
│   │   ├── test_checksum.py
│   │   └── test_hidden_masking.py # Validates FR-007 masking logic
│   └── integration/
│       └── test_full_loop.py
└── requirements.txt
```

**Structure Decision**: Single project structure under `code/` is selected to minimize overhead for a research script. All components (renderer, agent, scorer) are tightly coupled to the experiment flow. `data/` is split into `raw` (environment seeds) and `processed` (generated logs) to satisfy Data Hygiene principles. `utils/` contains dedicated scripts for checksumming, versioning, and validation to satisfy Constitutional requirements. `baseline_adapter.py` is added to handle the Visual-to-Structured conversion for the baseline.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Quantized Model on CPU | Required to run inference within 7GB RAM constraint (Constitution Principle VII). | Running full precision models would exceed RAM limits and fail on CI. |
| Sliding Window/Truncation | Required to handle context window limits when event logs grow (Edge Case: large ASCII). | Fixed context would cause errors in long-horizon tasks; truncation preserves recent history essential for immediate decisions. |
| Baseline Re-run (Visual) | Required to ensure "like-for-like" comparison of *modality* (Text vs. Visual) (FR-008 Override). | Using the original paper's visual results would introduce confounding variables (different seeds, different visual encoding). |
| Structured Metric | Required to avoid string-formatting noise (Constitution Principle II). | Raw Levenshtein distance penalizes phrasing differences rather than state retention errors. |
| Hidden State Masking | Required to isolate *retention* from *parsing* (FR-007). | Comparing full state would be dominated by visible items, invalidating the retention metric. |

## Implementation Phases

### Phase 1: Data Generation & Validation (FR-001, SC-005)
1.  **Implement Renderer**: `code/renderer.py` generates ASCII grids and JSON logs from RNG-Bench seeds.
2.  **Implement Validator**: `utils/renderer_validator.py` compares generated ASCII to visual ground truth (Levenshtein distance = 0).
3.  **Checksum Data**: `utils/checksum.py` is invoked on all files in `data/processed/` to generate and record checksums (Constitution III).
4.  **Verify**: Run `pytest tests/unit/test_renderer.py` and `test_hidden_masking.py`.

### Phase 2: Agent & Baseline Implementation (FR-002, FR-003, FR-008 Override)
1.  **Implement Agent Loop**: `code/agent_loop.py` loads quantized model, processes ASCII/Log, outputs Action + Mental Map.
2.  **Implement Baseline Adapter**: `code/baseline_adapter.py` parses Baseline MLLM (Visual) output into structured JSON.
3.  **Implement Scorer**: `code/scorer.py` calculates Memory Gap using Structured Diff + Masking.
4.  **Validate Masking**: Run `pytest tests/unit/test_hidden_masking.py` to ensure visible items are correctly excluded from `masked_ground_truth`.

### Phase 3: Experimental Execution & Power Analysis (FR-005, SC-003, SC-004)
1.  **Phase 3a: Pilot Run**: Execute multiple runs per condition (Text vs. Visual Baseline). Log RAM usage and execution time.
2.  **Phase 3b: Power Analysis**: Calculate effect size and variance from Pilot.
    - If effect size is small or variance high, **trigger scaling**: Re-run with N=64 per condition.
    - If effect size is large and variance low, proceed with N=20 as definitive.
3.  **Statistical Test**: Run Mann-Whitney U test on final dataset.

### Phase 4: Artifact Finalization (Constitution V)
1.  **Aggregate Results**: Combine logs into `results/statistical_summary.json`.
2.  **Hash Artifacts**: Invoke `utils/hasher.py` to generate SHA-256 hashes for all files in `data/processed/` and update `state/...yaml`.
3.  **Verify**: Run `pytest tests/` to ensure reproducibility.