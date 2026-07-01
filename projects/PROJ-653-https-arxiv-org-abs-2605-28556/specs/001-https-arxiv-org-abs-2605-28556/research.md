# Research: A Matter of TASTE: Improving Coverage and Difficulty of Agent Benchmarks

## 1. Executive Summary
This research validates the feasibility of reproducing the "A Matter of TASTE" paper within the constraints of a free-tier GitHub Actions runner (CPU-only, 7GB RAM, 6h). The core finding is that the TASTE pipeline (N-gram modeling, clustering, task synthesis) is computationally tractable without GPU acceleration, provided that the N-gram model operates on pre-seeded artifacts rather than training from raw text. 

Crucially, to address scientific soundness concerns, the evaluation of "difficulty" no longer relies on a single heuristic mock agent. Instead, it employs a **Multi-Heuristic Ensemble** (Regex, Exact Match, DistilBERT) and a **Proxy Validation Protocol** to ensure the "difficulty drop" is a robust measure of task complexity, not an artifact of a specific heuristic's bias.

## 2. Dataset Strategy

### 2.1 Verified Datasets & Artifacts
The project relies on **vendored artifacts** rather than external dataset downloads to ensure reproducibility and avoid network dependencies.

| Dataset/Artifact Name | Source/Location | Format | Relevance to Spec |
| :--- | :--- | :--- | :|
| `TASTE-task-synthesis-from-tool-sequence-evolution` | Vendored Submodule (Git) | Python Codebase | Contains the core N-gram, clustering, and synthesis logic (FR-001, FR-002). |
| `airline` Domain Config | `artifacts/domains/airline/tool_spec.json` | JSON | Defines available tools and constraints for the `airline` domain (FR-003). |
| `pre_seed.json` / `post_seed.json` | `artifacts/ngram/checkpoints/` | JSON | Pre-computed seed sequences for N-gram initialization (FR-001, Assumption 2). |
| `τ²-Bench` Baseline Tasks | `artifacts/baselines/t2_bench_airline.json` (Expected) | JSON | Baseline for difficulty comparison (SC-002, SC-005). |
| `Known LLM Failure Cases` | `artifacts/calibration/llm_failures.json` (Synthetic) | JSON | Curated set of tasks known to fail LLMs, used for Proxy Validation. |

**Dataset Fit Analysis**:
- **Variable Fit**: The `tool_spec.json` provides the necessary "predictors" (available tools) and "outcomes" (valid sequences) for the synthesis task. The `pre_seed.json` provides the "covariates" (seed sequences) for the N-gram model.
- **Missing Data**: The spec assumes `τ²-Bench` baseline tasks are available. If missing, the plan will generate a **Synthetic Baseline** using randomized tool sequences from `tool_spec.json` while preserving length distribution, ensuring SC-002 and SC-005 can still be measured.
- **No Fabrication**: No external URLs are cited as the project relies on local artifacts and the vendored submodule.

### 2.2 Data Processing Strategy
- **Normalization**: All tool sequences will be normalized to a canonical string representation (e.g., `tool_name(param1=val1)`) to ensure clustering consistency.
- **Sampling**: To stay within RAM limits, the N-gram sampling will be capped at [deferred] sequences per domain.
- **Validation**: The `airline.py` validator will act as a filter, discarding invalid sequences immediately to prevent accumulation of bad data.

## 3. Methodology & Statistical Rigor

### 3.1 N-gram Modeling (Stage 1)
- **Method**: Unigram/Bigram/Trigram probability estimation from seed sequences.
- **Statistical Rigor**:
    - **Entropy Check**: To address **Edge Case 1** (mode collapse), the plan calculates Shannon Entropy ($H = -\sum p(x) \log p(x)$) of the sampled distribution. If $H < 0.5$ (SC-003), the temperature parameter will be increased, and sampling re-run.
    - **Collinearity**: Since tools are discrete categories, collinearity is not a primary concern; however, the plan will track tool frequency to ensure no single tool dominates >90% of sequences.

### 3.2 Clustering (Stage 2)
- **Method**: K-Means or Hierarchical Clustering on vectorized tool sequences (TF-IDF or One-Hot encoding).
- **Statistical Rigor**:
    - **Cluster Count**: The spec mandates ≥5 clusters (FR-002). The plan will use the Elbow Method or Silhouette Score to justify the final $k$, but will enforce $k \ge 5$.
    - **Medoid Selection**: The actual tool sequence closest to the cluster centroid will be selected as the medoid to ensure representativeness.

### 3.3 Difficulty Evaluation (Stage 3) - **Revised Methodology**

#### 3.3.1 Multi-Heuristic Ensemble
Instead of a single mock agent, we deploy an ensemble of three diverse agents:
1.  **Regex Agent**: Matches simple patterns (e.g., "book flight").
2.  **Exact Match Agent**: Checks if the sequence matches a pre-defined valid path.
3.  **DistilBERT Agent**: A small, CPU-tractable Transformer fine-tuned on task planning (if feasible) or used as a zero-shot classifier for "plan coherence".

The **Difficulty Score** is defined as the **Consensus Failure Rate** (percentage of tasks where *all* agents fail). This decouples the metric from the specific failure mode of any single heuristic.

#### 3.3.2 Proxy Validation Protocol
To address the concern that heuristics do not approximate LLMs:
- **Step 1**: Run the Multi-Heuristic Ensemble on a curated set of `Known LLM Failure Cases` (from literature or the paper's supplementary materials).
- **Step 2**: Calculate the correlation coefficient ($r$) between the Ensemble's failure rate and the known LLM failure rate.
- **Step 3**: If $r < 0.6$, the ensemble is deemed invalid, and the plan halts with a warning. If $r \ge 0.6$, the ensemble is considered a valid proxy for the difficulty evaluation.

#### 3.3.3 Statistical Testing (Heuristic Complexity Gap)
- **Metric**: The **Heuristic Complexity Gap** is the difference in Consensus Failure Rates between TASTE tasks and Baseline tasks.
- **Statistical Test**: A **Permutation Test** is used to determine significance.
    - Null Hypothesis ($H_0$): The difference in failure rates is due to random chance.
    - Procedure: Shuffle task labels (TASTE vs. Baseline) multiple times and recalculate the gap.
    - Result: The p-value is the proportion of permutations where the gap is $\ge$ observed gap.
- **Effect Size**: Cohen's $d$ is calculated to measure the magnitude of the gap, replacing the arbitrary "30 percentage point" target.
- **Orthogonal Validation**: We also correlate the "Difficulty Score" with "Tool Sequence Entropy". A high correlation confirms that the difficulty is driven by structural complexity, not content bias.

### 3.4 Baseline Generation Strategy
If `τ²-Bench` is missing:
1.  Load `tool_spec.json`.
2.  Generate random tool sequences of lengths matching the TASTE distribution.
3.  Ensure these sequences are syntactically valid but logically simple (low entropy).
4.  This synthetic baseline ensures the comparison is always computable and controlled.

## 4. Computational Feasibility

- **Memory**: N-gram models on tool sequences (typically <10 tools) are lightweight. Clustering 10k items on 2 cores is feasible within 7GB RAM. DistilBERT inference on a small batch of tasks is CPU-tractable.
- **Runtime**: The pipeline is linear. Sampling (seconds), Clustering (minutes), Validation (minutes), Ensemble Evaluation (minutes). Total time < 2 hours, well within the 6h limit.
- **No GPU**: All operations use `numpy`, `scikit-learn`, and CPU-optimized `transformers` in CPU mode. No CUDA dependencies.

## 5. Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Mode Collapse** | N-gram generates repetitive tasks, failing SC-003. | Implement entropy check and temperature ramping (Edge Case 1). |
| **Validator Mismatch** | `tool_spec.json` lists tools not in `airline.py`. | Raise `ConfigurationError` at startup (Edge Case 2, FR-006). |
| **Low Validity Rate** | <80% tasks pass validation (SC-001). | Implement retry loop with parameter perturbation; if persisting, log and report as a limitation. |
| **Missing Baseline** | `τ²-Bench` tasks not found. | Generate synthetic baseline with random tool sequences of comparable length (Phase 2, Step 2.5). |
| **Proxy Failure** | Ensemble does not correlate with LLM failures ($r < 0.6$). | Halt execution and report "Proxy Validation Failed" (Phase 3, Step 3.3.2). |

## 6. Decision Rationale
The decision to use a **Multi-Heuristic Ensemble** and **Proxy Validation Protocol** is driven by the need for scientific rigor in the absence of live LLMs. By using diverse agents and calibrating them against known failure modes, we ensure that the "difficulty" metric is a robust measure of task complexity, not an artifact of a single heuristic's bias. The **Permutation Test** provides a statistically valid foundation for the "difficulty drop" claim without relying on arbitrary thresholds.
