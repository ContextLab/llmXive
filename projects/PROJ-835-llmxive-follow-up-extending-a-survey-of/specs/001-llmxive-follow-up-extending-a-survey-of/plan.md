# Implementation Plan: LLMXive Follow-up: Extending "A Survey of Large Audio Language Models" (Latent Anomaly Detection)

**Branch**: `001-gene-regulation` | **Date**: 2026-07-12 | **Spec**: `specs/001-gene-regulation/spec.md`
**Input**: Feature specification from `specs/001-gene-regulation/spec.md`

## Summary

This feature implements a CPU-only pipeline to investigate whether statistical anomalies in the latent embedding space of frozen audio encoders correlate with cross-modal jailbreak attempts. The approach involves extracting fixed-dimensional embeddings from labeled audio-text pairs (benign vs. jailbreak) using a distilled Whisper Base encoder, calculating Mahalanobis distances from a benign centroid (derived strictly from the training set), and training a lightweight Logistic Regression classifier. To address methodological rigor, the plan includes a random noise baseline to avoid tautological validation. The entire pipeline is constrained to run on a GitHub Actions free-tier runner (CPU cores, 7 GB RAM, ≤6 hours) without GPU acceleration.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `transformers` (CPU-only), `torch` (CPU-only), `scikit-learn`, `pandas`, `datasets`, `numpy`, `soundfile`  
**Storage**: Local filesystem (`data/` for raw/processed data, `models/` for artifacts, `results/` for reports, `state/` for versioning)  
**Testing**: `pytest` with contract validation against YAML schemas  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Computational research pipeline / CLI  
**Performance Goals**: Total runtime < 6 hours; Peak RAM < 7 GB; Embedding extraction < 15 mins for 100 samples  
**Constraints**: NO GPU/CUDA; NO deep-net training; NO 8-bit/4-bit quantization requiring CUDA; strict adherence to dataset-variable fit (verified labels independent of encoder stats); strict data separation (training vs. test) for statistics.  
**Scale/Scope**: Processing a subset of verified LALM adversarial datasets (approx. k to memory-constrained scale); single-node execution.

> Domain-specific empirical specifics (exact sample counts, measured runtimes) are deferred to the research/implementation phase.

## Constitution Check

| Principle | Status | Action / Verification |
| :--- | :--- | :--- |
| **I. Reproducibility** | PASS | Plan mandates pinned `requirements.txt`, fixed random seeds, and deterministic data fetching from verified URLs. |
| **II. Verified Accuracy** | PASS | Plan restricts dataset sources to the "Verified datasets" block in the spec. No external URLs will be invented. |
| **III. Data Hygiene** | PASS | Plan includes checksumming of downloaded datasets and separation of raw vs. derived data. |
| **IV. Single Source of Truth** | PASS | All metrics (Precision, Recall, F1, Mahalanobis r) derived from `code/` execution, not hand-typed. |
| **V. Versioning Discipline** | PASS | Plan explicitly includes a step to write artifact hashes to `state/projects/PROJ-835-llmxive-follow-up-extending-a-survey-of.yaml` after each major phase. |
| **VI. CPU-Only Inference** | PASS | Plan explicitly selects `torch` CPU wheels and `distil-whisper` (or similar) without CUDA flags. |
| **VII. Latent-Space Protocol** | PASS | Plan centers on Mahalanobis distance and Logistic Regression on embeddings, not retraining the encoder. Includes random noise baseline to avoid tautology. |

## Project Structure

### Documentation (this feature)

```text
specs/001-gene-regulation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    └── embedding.schema.yaml
```

### Source Code (repository root)

```text
src/
├── data/
│   ├── download.py          # Fetches verified datasets
│   ├── preprocess.py        # Handles audio loading, error skipping (FR-005), label validation
│   └── embed.py             # Extracts frozen encoder embeddings (FR-001)
├── models/
│   ├── train.py             # Logistic Regression training (FR-002)
│   └── eval.py              # Metrics, baseline comparison, resource logging (FR-003, FR-004)
├── utils/
│   ├── stats.py             # Mahalanobis distance calculation with Ledoit-Wolf (FR-006)
│   └── config.py            # Random seeds, paths, state file management
└── cli/
    └── run_pipeline.py      # Orchestrates download -> embed -> train -> eval -> state-update

tests/
├── contract/
│   ├── test_dataset_schema.py
│   └── test_embedding_schema.py
├── unit/
│   └── test_stats.py
└── integration/
    └── test_full_pipeline.py
```

**Structure Decision**: Single project structure (`src/`) chosen to simplify data flow for a research pipeline. No separate frontend/backend required. `cli/` ensures end-to-end reproducibility.

## Phase Breakdown & FR/SC Mapping

### Phase 0: Data Acquisition, Verification & Label Validation
*   **Goal**: Download, verify integrity, and validate label independence of verified datasets.
*   **FR Coverage**:
    *   **FR-007**: Verify ground truth independence (check dataset documentation for labeling methodology).
    *   **FR-005**: Implement robust loading (skip corrupted files).
    *   **Label Validation**: Explicitly verify that 'jailbreak' labels are not derived from encoder statistics.
*   **SC Coverage**:
    *   **SC-002**: Log start time.
*   **Steps**:
    1.  Fetch datasets from verified URLs (LALM Adversarial subsets, if available; otherwise, fallback to verified benign TTS + random noise generation).
    2.  Compute SHA-256 checksums; validate against `state/projects/PROJ-835-llmxive-follow-up-extending-a-survey-of.yaml` `artifact_hashes` map.
    3.  **Label Validation**: Inspect metadata to confirm `jailbreak`/`benign` labels exist. If labels are ambiguous (e.g., "emotional damage"), map them only if the definition aligns with adversarial intent. If not, exclude the dataset or use it only for benign baseline construction.
    4.  Define `state` file schema: `artifact_hashes` map where keys are file paths and values are SHA-256 strings.

### Phase 1: Embedding Extraction (CPU-Only)
*   **Goal**: Extract fixed-dimensional vectors using frozen encoder.
*   **FR Coverage**:
    *   **FR-001**: Extract embeddings on CPU, no CUDA.
    *   **FR-005**: Skip corrupted audio, log errors.
*   **SC Coverage**:
    *   **SC-002**: Monitor time per batch.
*   **Steps**:
    1.  Load `distil-whisper-base` (output dimension appropriate to the chosen model architecture, matching `AudioEmbedding` contract within the expected range) in `torch.no_grad()` mode, device=`cpu`.
    2.  Iterate batches (size=32).
    3.  Save embeddings + labels to `data/embeddings.parquet`.
    4.  **Dimension Check**: Verify output dimension is consistent with the model specification.

### Phase 2: Anomaly Scoring, Classification & Baseline Testing
*   **Goal**: Compute Mahalanobis distance (with regularization), train classifier, and test against random noise.
*   **FR Coverage**:
    *   **FR-002**: Train Logistic Regression (We will employ a standard train-test split. The research question remains: [Research Question]. The method will be: [Method]. References: [Citations].).
    *   **FR-006**: Calculate Mahalanobis distance from benign centroid (stored as `AnomalyScore` entity).
*   **SC Coverage**:
    *   **SC-005**: Calculate Pearson correlation (r) between Mahalanobis distance and labels.
    *   **SC-004**: Compare F1 against stratified random baseline.
*   **Steps**:
    1.  **Strict Data Split**: Split data into Train (majority) and Test (minority) **before** any statistical calculation.
    2.  **Centroid Calculation**: Compute mean $\mu_{benign}$ and covariance $\Sigma$ **only** from the **Training Set's** benign samples.
        *   **Regularization**: Use `LedoitWolf` covariance estimator to handle high dimensionality vs. sample size.
    3.  **Anomaly Scoring**: Calculate Mahalanobis distance for all samples (Train and Test) using $\mu_{benign}$ and $\Sigma$ from Step 2. Store results as `AnomalyScore` entity.
    4.  **Random Noise Baseline**: Generate synthetic random noise vectors (Gaussian, same dim) and calculate their distance to $\mu_{benign}$ to establish a general audio manifold baseline.
    5.  Train `LogisticRegression` (CPU, no GPU) on Train set embeddings.
    6.  Generate predictions and probabilities for Test set.

### Phase 3: Evaluation, Reporting & State Update
*   **Goal**: Generate metrics, resource logs, and update versioning state.
*   **FR Coverage**:
    *   **FR-003**: Evaluate Precision, Recall, F1.
    *   **FR-004**: Log RAM usage and total wall-clock time.
*   **SC Coverage**:
    *   **SC-001**: Measure Recall against ground truth.
    *   **SC-002**: Verify total time < 6 hours.
    *   **SC-003**: Verify RAM < 7 GB.
*   **Steps**:
    1.  Compute metrics.
    2.  Profile memory (using `tracemalloc` or `psutil`).
    3.  Write `results/report.md` and `results/resource_log.json`.
    4.  **State Update**: Compute SHA-256 hashes for all output artifacts (embeddings, models, reports) and update `state/projects/PROJ-835-llmxive-follow-up-extending-a-survey-of.yaml` `artifact_hashes` map.

## Compute Feasibility Strategy

- **Memory Management**: Process audio in batches of a fixed size. If RAM approaches a high threshold, reduce batch size to. Use `float32` (default) but avoid storing full intermediate tensors.
- **CPU Optimization**: Use `The number of threads will be configured to a fixed integer value.

Research Question: How does thread configuration impact computational efficiency in PyTorch workflows?
Method: Controlled experiments varying thread settings while measuring execution time.
References: Paszke et al. (2019)` to match the runner. Disable CUDA (`os.environ["CUDA_VISIBLE_DEVICES"]=""`).
- **Dataset Sampling**: If the full LALM dataset exceeds memory/time limits, the plan will implement a stratified random sampling step (e.g., A large sample size will be utilized.) *before* embedding extraction to ensure the 6-hour limit is met.
- **Library Pins**: `torch` (CPU wheel), `transformers` (latest stable), `scikit-learn` (latest).
- **Covariance Regularization**: Use `LedoitWolf` to ensure mathematical validity when $N_{samples} < N_{dimensions}$.