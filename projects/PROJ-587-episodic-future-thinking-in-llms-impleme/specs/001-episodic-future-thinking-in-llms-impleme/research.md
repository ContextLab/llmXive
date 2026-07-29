# Research: Episodic Future Thinking in LLMs

## 1. Problem Statement & Scientific Rationale

The core hypothesis is that LLM architectures augmented with explicit episodic memory modules (storing specific (state, action, outcome) tuples) will outperform standard transformers in planning tasks that require "mental time travel"—simulating future scenarios based on specific past experiences rather than general semantic knowledge. This addresses the critique that standard transformers merely perform statistical pattern completion (WYSIATI bias) rather than true episodic recollection.

**Key Scientific Question**: Does the architectural addition of a neural episodic control module enable more accurate future scenario simulation, and does this generalize across tasks requiring episodic retrieval?

## 2. Theoretical Framework

### 2.1 Episodic vs. Semantic Memory
Drawing from Tulving's distinction and Pritzel et al. (2017), we distinguish:
- **Semantic Memory**: General world knowledge (e.g., "keys open doors").
- **Episodic Memory**: Specific events bound to time and context (e.g., "I picked up the key in the kitchen at 10:00 AM").

The proposed architecture implements a "synaptic locus" for episodic memory via a key-value store indexed by semantic embeddings of states and actions, allowing for the retrieval of specific trajectories. This addresses the concern raised by simulated Eric Kandel regarding the need for a specific mechanism for memory storage rather than a diffuse statistical distribution.

### 2.2 Mental Time Travel & Simulation
Per the Scrub Jay analogy (David Krakauer) and Peak-End Rule (Daniel Kahneman), the system must simulate future states by combining retrieved episodic fragments with current context. The validation protocol (US-3) specifically tests for the system's ability to distinguish known episodic details from unknown counterfactuals, addressing the "WYSIATI" bias. The architecture includes a **Forward Simulation** mechanism (learned transition model) to explicitly operationalize "simulation" rather than just recall.

## 3. Dataset Strategy

We utilize ALFWorld and TextWorld benchmarks, which provide explicit temporal markers and ground-truth trajectories necessary for constructing (state, action, outcome) tuples. All datasets are open, directly downloadable, and do not require credentials.

| Dataset | Source (Verified) | Usage | Relevance to Variables |
|:--- |:--- |:--- |:--- |
| **ALFWorld** | `https://huggingface.co/datasets/alfworld/alfworld` (test split) | Held-out tasks for evaluation. | Provides ground-truth solutions for accuracy measurement (SC-001). |
| **ALFWorld (Train)** | `https://huggingface.co/datasets/alfworld/alfworld` (train split) | Source of planning trajectories (state, action, outcome) for memory storage. | Contains explicit step IDs and temporal sequences required for episodic reconstruction. |
| **TextWorld** | ` (raw environment data) | Disjoint state manifold for Zero-Shot control. | Offers varied narrative structures to test generalization of episodic retrieval. |

**Data Availability Note**: ALFWorld is fetched via the `datasets` library. TextWorld is fetched from the official GitHub repository. Both are compatible with streaming to fit within the disk constraint.

## 4. Methodology

### 4.1 Architecture Design
- **Baseline**: A 70M parameter Transformer (CPU-optimized) trained on the benchmark tasks.
- **Episodic Model**: The baseline architecture augmented with a Neural Episodic Control (NEC) module.
 - **Memory Store**: FAISS HNSW index storing embeddings of (state, action, outcome) tuples.
 - **Retrieval**: Cosine similarity search with a fixed operational threshold of 0.75 (FR-002).
 - **Integration**: Retrieved episode embeddings are concatenated with the current state embedding before the attention layers.
 - **Forward Simulation**: The model uses retrieved past states to predict the *next* state via a learned transition model, explicitly operationalizing "simulation" rather than just recall.

### 4.2 Experimental Design
- **Tasks**: 50 held-out planning tasks from ALFWorld/TextWorld, selected for episodic necessity (hidden state changes).
- **Conditions**:
 1. Baseline Transformer (No episodic memory).
 2. Episodic-Augmented Transformer (Full retrieval).
 3. Episodic-Augmented (Sensitivity Sweep: thresholds 0.70, 0.75, 0.80).
 4. Zero-Shot Control (Test on disjoint TextWorld tasks to prove retrieval efficacy).
- **Metrics**:
 - **Accuracy**: Task success rate (SC-001).
 - **Retrieval Precision**: Top-5 relevance (SC-002).
 - **Confidence Calibration**: Flagging rate of counterfactual details (SC-003).
 - **Coherence**: Human evaluation ratings (SC-004).

### 4.3 Statistical Analysis Plan
- **Primary Test**: Mixed-effects modeling (lme4-style) with `task_id` as a random effect to account for task difficulty variance.
 - **Model**: `Accuracy ~ Condition + Retrieval_Precision + (1|task_id)`
 - **Correction**: Bonferroni correction applied if ≥10 task variants are tested (FR-008).
 - **Fallback**: Permutation tests if Shapiro-Wilk test p-value < 0.05 (FR-004).
- **Power Analysis**: Pre-registered target of n=10 task *variants* (random effect groups), α=0.05, power=0.80, detectable effect size d=0.8. A **Pilot Study** (n=5 tasks) will be conducted first to empirically estimate variance components before finalizing the power analysis.
- **Sensitivity Analysis**: Explicit sweep of similarity thresholds ∈ {0.70, 0.75, 0.80} to verify robustness (FR-006).

### 4.4 Counterfactual Generation Protocol
- **Method**: Counterfactual details are generated by swapping outcome values from *unrelated* stored episodes (not random noise) to create "known-unknowns".
- **Verification**: The ground truth of these perturbed details is verified against the original source episodes to ensure the "known-unknown" status is accurate. This ensures construct validity for confidence calibration.

### 4.5 Human Evaluation Protocol
- **Execution**: For the final paper and SC-004, a **Human Evaluation** phase is defined. This involves recruiting ≥3 raters, collecting 1-5 Likert scale ratings for scenario coherence, and calculating inter-rater reliability. This replaces "simulated" ratings to satisfy the requirement for human evaluation.

## 5. Compute Feasibility

- **CPU-First Strategy**: All training and inference will run on CPU using `faiss-cpu` and `torch` (CPU build).
- **Memory Management**:
 - Dataset streaming (`datasets.load_dataset(..., streaming=True)`) to avoid loading full datasets into RAM.
 - FAISS index built incrementally to stay within 7GB RAM.
 - **Quantized Embeddings**: Use a quantized embedding model and batched processing to ensure the 7GB RAM constraint is met with the cited datasets., addressing the memory feasibility concern.
- **No GPU Fabrication**: No synthetic CPU approximations of GPU tasks. If a specific operation requires GPU (e.g., large-scale embedding generation), it will be scaled down to a representative subset or offloaded to the Kaggle GPU escape hatch if the code explicitly detects CUDA requirements (though the plan prioritizes CPU-only execution).

## 6. Decision/Rationale

| Decision | Rationale |
|:--- |:--- |
| **FAISS HNSW over Linear Scan** | Required to meet the ≤500ms retrieval latency constraint (FR-001) with ≥10k entries on CPU. |
| **Fixed Threshold 0.75 with Sweep** | Operational threshold fixed at 0.75 per FR-002; sensitivity sweep (0.70, 0.75, 0.80) ensures robustness and addresses FR-006 explicitly. |
| **Mixed-Effects Modeling** | Necessary to handle hierarchical data structure (tasks within environments) and avoid inflated Type I errors (FR-004). |
| **Streaming Data Loading** | Essential to process large datasets within 7GB RAM constraint without truncation or fabrication. |
| **Counterfactual Validation** | Addresses the "WYSIATI" and "Statistical vs. Episodic" concerns by testing confidence on known-unknowns (unrelated episode swaps). |
| **Zero-Shot Control** | Distinguishes retrieval efficacy from statistical memorization by testing on a disjoint state manifold (TextWorld). |
| **Pilot Study** | Empirically estimates variance components before final power analysis, resolving circularity. |
| **Quantized Embeddings** | Ensures 7GB RAM compliance with large datasets. |
| **Human Evaluation Protocol** | Provides a valid CI validation path for coherence scoring while acknowledging the need for human data in the final paper. |
