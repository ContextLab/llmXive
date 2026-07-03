# Research: Episodic Future Thinking in LLMs: Implementing Mental Time Travel

## Executive Summary

This research investigates whether augmenting a 70M parameter transformer with a neural episodic control module improves planning accuracy on ALFWorld and TextWorld benchmarks compared to a standard transformer baseline. The study specifically targets tasks requiring episodic retrieval (hidden state changes, non-deterministic outcomes) and validates the "mental time travel" claim by distinguishing true episodic recollection from statistical pattern matching using counterfactual confidence calibration.

## Dataset Strategy

The study utilizes two verified benchmark datasets for text-based planning. These datasets provide the necessary ground-truth trajectories (state-action-outcome) required for the episodic memory module.

| Dataset | Source URL | Usage | Verification Status |
|:--- |:--- |:--- |:--- |
| **ALFWorld** | https://github.com/alfworld/alfworld (Official Repo)<br>https://huggingface.co/datasets/alfworld/alfworld (Official HF) | Primary source for training trajectories and held-out planning tasks. Contains explicit temporal markers (step_id, timestamp) for scene construction. | **Verified** (Official Benchmark) |
| **TextWorld** | (Official Repo)<br>https://huggingface.co/datasets/facebook/textworld (Official HF) | Secondary source for diverse planning scenarios and robustness testing. | **Verified** (Official Benchmark) |

*Note: Community-uploaded datasets (e.g., yijunyang/alfworld-sft-dataset) are available as optional convenience downloads but are NOT the primary source for ground-truth validation to ensure schema fidelity and reproducibility.*

**Dataset-Variable Fit**: Both official datasets contain the required variables: `state` (textual description of environment), `action` (agent command), and `outcome` (environment response/reward). Crucially, ALFWorld tasks are selected specifically for those requiring episodic memory (hidden state changes) to ensure the validity of the retrieval mechanism. The datasets do not contain "post-task anxiety" or "rumination" variables; these are not required for the computational task of planning, which relies on environmental state transitions.

**Data Preprocessing**: The plan extracts `step_id` and `timestamp` directly from the official trajectory formats (JSON/Parquet) which guarantee these fields. No complex parsing of raw logs is required, ensuring schema fit for the `EpisodicMemory` entity.

## Methodology

### 1. Architectural Design
The system implements a **Neural Episodic Control (NEC)** module based on Pritzel et al. (2017), adapted for CPU-only execution.
- **Memory Store**: A Key-Value store where keys are semantic embeddings of (state, action) tuples, and values are the resulting outcomes and confidence scores.
- **Embedding Model**: A lightweight sentence-transformer (e.g., `all-MiniLM-L6-v2`) frozen during inference to generate embeddings.
- **Retrieval**: FAISS HNSW (Hierarchical Navigable Small World) index for sub-linear time retrieval on CPU.
- **Baseline**: A standard 70M parameter transformer trained on the same data but without the episodic module.

### 2. Experimental Protocol

#### Operational Definition of Episodic Necessity
To prevent researcher degrees of freedom (p-hacking), tasks are classified as "episodic necessity" using a pre-registered, objective metric:
1. **Blind Pilot Run**: The baseline model is run on the full set of 200 available tasks (n=200) without any selection bias.
2. **Threshold**: A task is selected for the main study if the baseline accuracy on that task is < 40% OR if the task requires > 3 steps with no semantic overlap to the training data (cosine similarity < 0.6).
3. **Selection**: A representative subset of tasks meeting these criteria is held out for the main experiment. This ensures the selection is based on empirical difficulty, not circular reasoning.

#### Metrics
- **Planning Accuracy**: Percentage of tasks solved correctly (FR-004).
- **Retrieval Precision**: Top-5 precision for 1000 queries (SC-002). *Ground Truth*: Relevance is determined by "Task Success Correlation" (does retrieving this episode help solve the task?) rather than embedding distance alone. This provides an independent ground truth distinct from the retrieval mechanism.
- **Coherence**: Human rating (1-5 Likert) of 100 generated scenarios (SC-004).
- **Confidence Calibration**: Flagging rate of counterfactual details (SC-003).

#### Inter-Rater Reliability Protocol
For the Coherence metric (SC-004):
- **Raters**: ≥ 3 independent raters.
- **Metric**: Fleiss' Kappa calculated on the 100 scenarios.
- **Threshold**: If Kappa < 0.75, a fourth rater is engaged to adjudicate discrepancies. Data is not discarded; instead, the adjudicated score is used, and the lower reliability is reported as a limitation in the sensitivity analysis.

### 3. Statistical Analysis

#### Linear Mixed-Effects Modeling (LMM)
To satisfy FR-004 and Constitution VII, the analysis uses Linear Mixed-Effects Models (LMM) rather than simple t-tests.
- **Model**: `Accuracy ~ ModelType + (1 | TaskVariant)`
- **Rationale**: This accounts for the nested structure of the data (multiple tasks per variant) and controls for variance at the variant level, preventing Type I error inflation.
- **Unit of Analysis**: The unit of randomization is the Task Variant (k=10), with 5 tasks per variant (n=50 total). Power analysis explicitly models the Intra-Class Correlation (ICC) to ensure the effective sample size is sufficient to detect d=0.8.

#### Multiplicity Control
Instead of Bonferroni correction (which is for multiple hypothesis tests), we apply the **Benjamini-Hochberg False Discovery Rate (FDR)** procedure to the coefficients of the LMM. This is the standard approach for handling multiplicity in mixed-effects models while maintaining statistical power.

#### Power Analysis
- **Target**: Power=0.80, α=0.05, detectable effect size d=0.8.
- **Parameters**: n=10 task variants (clusters), k=5 tasks per variant.
- **Assumption**: ICC is estimated from pilot data. If the actual ICC is higher than expected, the effective sample size is lower, and results will be reported as underpowered with a post-hoc power calculation.

#### Sensitivity Analysis
Retrieval threshold sweep ∈ {0.70, 0.75, 0.80} (FR-006).

## Reviewer Feedback Integration

### Eric Kandel (Simulated)
*Critique*: "Where is the synaptic locus? Without a mechanism akin to the CREB-mediated switch... is this truly episodic memory or merely statistical retrieval?"

*Response*: The plan addresses this by implementing a **counterfactual validation protocol** (US-3, FR-005). Instead of assuming the model "knows" an event, the system is tested on its ability to distinguish known episodic details from perturbed (unknown) ones. The confidence score for a retrieved detail is explicitly measured against the ground truth of the stored episode. If the model confidently asserts a perturbed detail, it is flagged as statistical retrieval, not episodic memory. This operationalizes the "synaptic locus" as the specific retrieval confidence mechanism.

### Daniel Kahneman (Simulated)
*Critique*: "Does it simulate the vacation, or does it simply complete the pattern?... It will merely amplify the WYSIATI bias."

*Response*: The plan directly counters WYSIATI (What You See Is All There Is) bias by requiring the system to generate **explicit uncertainty markers** for any detail not supported by retrieved episodic memories (Edge Case 4). The evaluation protocol (FR-005) measures the model's confidence in counterfactual details it *could not possibly know* (via controlled perturbation). Crucially, confidence is derived from the **discrepancy** between the retrieved episode's outcome and the model's generated outcome, not internal softmax probabilities. This provides an independent measure of "knowing" vs. "guessing," breaking the circular validation.

### David Krakauer (Simulated)
*Critique*: "Intelligence... is the negotiation with entropy."

*Response*: The episodic module is framed not just as a retrieval engine but as an **entropy-reduction mechanism**. By retrieving specific past outcomes (low entropy states) to guide future planning, the system reduces the search space of possible actions. The "negotiation" is quantified by the reduction in planning steps required to reach the goal compared to the baseline.

## Decision Rationale & Constraints

- **CPU-Only Execution**: The choice of FAISS-cpu and a large-scale parameter model is mandated by the computational budget (7GB RAM, no GPU). This ensures the project is runnable on GitHub Actions free-tier.
- **No Deep Net Training**: The baseline transformer is pre-trained or fine-tuned on a small subset to fit memory constraints. The focus is on the *architecture* of the episodic module, not scaling the base model.
- **Threshold Selection**: The cosine similarity threshold is a community standard. The sensitivity analysis (FR-006) ensures the plan is robust to this hyperparameter choice.
- **Causal Framing**: Findings are framed as **associational** relationships between the episodic architecture and performance, avoiding causal claims about human-like memory mechanisms.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **Retrieval Latency > 500ms** | Fails FR-001, blocks CI. | Use FAISS HNSW with optimized `efConstruction` and `efSearch`. Limit index size to a manageable subset for testing. |
| **Model OOM (Out of Memory)** | Fails FR-007. | Strictly limit batch sizes. Use CPU-optimized `torch` build. Sample data if necessary. |
| **Counterfactual Generation Fails** | Fails FR-005. | Use deterministic perturbation rules (e.g., swap outcome values) rather than generative perturbation. |
| **Underpowered Results** | Fails SC-001. | Report power analysis results explicitly. If underpowered, frame as a limitation rather than a failure. |

