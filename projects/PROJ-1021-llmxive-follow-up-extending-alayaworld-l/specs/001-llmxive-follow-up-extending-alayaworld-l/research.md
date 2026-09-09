# Research: llmXive follow-up: extending "AlayaWorld: Long-Horizon and Playable Video World Generation"

## Research Question
How does the integration of a lightweight, CPU-tractable symbolic logic layer influence the long-horizon semantic consistency of interactive video world models compared to autoregressive generation alone?

## Dataset Strategy

| Dataset | Source / URL | Access Method | Feasibility Note |
| :--- | :--- | :--- | :--- |
| **AlayaWorld** | **NO VERIFIED SOURCE** | Programmatic loader (assumed) | **CRITICAL RISK**: No verified URL found in the project's verified datasets block. The plan assumes the model weights and sample sequences are available via a local path or a specific, non-verified loader. If no open download exists, the implementation cannot proceed with real data. The plan includes a fallback to a "mock" video generator for *unit testing* (CV pipeline validation, symbolic engine logic), but the primary research question regarding *generative* drift cannot be answered with mock data. If the dataset is unavailable, the study will be limited to a "Methodological Validation" report. |

**Strategy**:
1.  **Ingestion**: Attempt to load `alaya_world_v1` via `datasets.load_dataset("alaya_world")` (if a HF repo exists) or a local path.
2.  **Fallback (Unit Test Only)**: If no open source is found, the system will generate synthetic video frames (using a simple procedural generator) to validate the *symbolic engine* and *CV pipeline* logic. The "Semantic Drift Score" will be calculated on this synthetic data, but the results will be labeled "Methodological Validation Only" and not used for the primary hypothesis test.
3.  **Streaming**: If the dataset is large, `streaming=True` will be used to process frames one-by-one to stay within 7GB RAM.
4.  **Feasibility Gate**: If the dataset is not found, the main experiment is aborted, and a "Methodological Validation" report is generated.

## Methodology

### Phase 1: Baseline Semantic Drift Quantification (US-1)
- **Input**: 10 action sequences, frozen AlayaWorld model (quantized).
- **Process**:
  1.  Generate video sequences of moderate duration.
  2.  Run deterministic symbolic engine (seed 42) to produce ground-truth state logs.
  3.  Run CV pipeline (sparse optical flow, color histograms) on generated frames to extract visual states.
  4.  Validate CV pipeline against 50 manually annotated frames (FR-007). If accuracy < 85%, flag as invalid.
  5.  Calculate "Semantic Drift Score" (visual vs. logical divergence) using **validated** visual states.
- **Output**: `data/results/baseline_scores.json`.

### Phase 2: Hybrid Correction Mechanism (US-2)
- **Input**: Same 10 action sequences.
- **Process**:
  1.  Enable symbolic engine.
  2.  At each frame generation step, compare symbolic state with predicted visual state.
  3.  If discrepancy detected (e.g., object HP=0 but visual object present), inject "correction token" (prompt update).
  4.  Regenerate sequence with correction.
  5.  Re-run CV pipeline and calculate new drift score.
- **Output**: `data/results/hybrid_scores.json`.

### Phase 3: Statistical Analysis (US-1, US-2)
- **Test**: Paired Wilcoxon signed-rank test on baseline vs. hybrid drift scores across multiple seeds.
- **Pre-checks**:
  1.  **Normality**: Shapiro-Wilk test on the *paired differences* (Baseline - Hybrid). If p > 0.05, data is non-normal, justifying Wilcoxon.
  2.  **Variance Stability**: Calculate rolling variance of frame-level error series. Flag if variance is excessive, but proceed (Wilcoxon is robust).
- **Metric**: p-value < 0.05 indicates significant reduction in drift.
- **Note**: The Augmented Dickey-Fuller (ADF) test has been **removed** as it is statistically invalid for bounded, discrete frame-level error series and is not required for the Wilcoxon test.

### Phase 4: Resource Constraint Verification (US-3)
- **Process**: Run full hybrid pipeline on CPU-only runner.
- **Metrics**: Log peak RAM (MB) and wall-clock time (seconds) per sequence.
- **Thresholds**: ≤ 7GB RAM, ≤ 30 minutes per sequence.

## Decision Rationale

| Decision | Rationale |
| :--- | :--- |
| **CPU-First, Quantized Model** | The project explicitly targets edge devices (multi-core CPU, sufficient RAM). Using a GPU-only model or full-precision weights would violate the core constraint (US-3). Quantization (low-bit) is the only faithful CPU-tractable form for a transformer-based video model. |
| **Sparse Optical Flow vs. Template Matching** | Template matching fails when object appearance changes (semantic drift). Sparse optical flow tracks motion vectors even under visual changes, providing a robust signal for state continuity. |
| **Symbolic Engine in Pure Python** | Ensures determinism (Constitution Principle VI) and avoids dependencies on external C++ libraries that might introduce non-determinism or overhead. |
| **No GPU Escape Hatch** | The research question is specifically about *CPU-tractable* solutions. A GPU-based solution would not answer the research question and would violate the "Edge-Device" constraint. |
| **Statistical Method (Shapiro-Wilk + Wilcoxon)** | The ADF test is invalid for bounded, discrete frame-level errors. Shapiro-Wilk on paired differences is the correct non-parametric check for Wilcoxon assumptions. |

## Dataset Variable Fit & Feasibility

- **Required Variables**: Object states (HP, inventory, position), user actions.
- **Dataset Check**: The "AlayaWorld" dataset is **not verified**.
  - **Risk**: If the dataset does not contain the specific object states or actions required, the symbolic engine cannot be grounded.
  - **Mitigation**: The symbolic engine will be designed to be generic (e.g., "Object A", "Object B") and mapped to the dataset's available entities. If the dataset lacks *any* object state information, the project will be flagged as "Data Unavailable" and the research question reframed to "Methodological Validation".
- **Conclusion**: The plan proceeds assuming the dataset contains the necessary action/state pairs. If not, the implementation will fail at the data loading step, and the report will explicitly state "Dataset Variable Mismatch: Required variables not found in AlayaWorld."
