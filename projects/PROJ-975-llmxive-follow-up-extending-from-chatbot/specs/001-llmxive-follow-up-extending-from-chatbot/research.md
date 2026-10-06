# Research: llmXive follow-up: extending "From Chatbot to Digital Colleague: The Paradigm Shift Toward Persistent"

## Objective

To empirically determine the "tipping point" of library size where retrieval noise degrades the performance of a "Digital Colleague" agent, and to evaluate whether an active "Skill Pruning" heuristic can mitigate this degradation.

## Methodology

### 1. Synthetic Environment Construction (FR-001, FR-002)

**Rationale**: Real-world codebases lack the deterministic ground truth required to measure "retrieval noise" vs. "solution validity" in isolation. A synthetic environment allows precise control over semantic overlap and task complexity.

**Dataset Strategy**:
- **Source**: Programmatically generated (no external download required).
- **Variables**:
  - `task_id`: Unique identifier.
  - `ground_truth_skills`: List of 3-5 skill IDs required to solve the task (deterministic).
  - `complexity`: Number of steps (3-5).
  - `skill_library`: Set of 100 skills with embeddings.
- **Overlap Control**:
  - Embeddings generated using `sentence-transformers/all-MiniLM-L6-v2` (CPU-optimized).
  - **Low Overlap**: Mean pairwise cosine < 0.30.
  - **Medium Overlap**: Mean pairwise > 0.50, 30% pairs > 0.50.
  - **High Overlap**: Mean pairwise > 0.80, 30% pairs > 0.80.
- **Feasibility**: 100 skills x 768 dimensions fits easily in RAM. 500 tasks x 5 steps is computationally trivial on CPU.

### 2. Agent Execution Loop (FR-003)

**Rationale**: To measure the causal effect of library size on performance.

**Experimental Design**:
- **Independent Variables**:
  - Library Size: 10, 30, 50, 100 (subset of the 100-skill library).
  - Pruning: Enabled vs. Disabled.
  - Overlap Level: Low, Medium, High.
- **Dependent Variables**:
  - Task Success Rate (binary: success/fail).
  - Latency (ms).
  - Token Usage (estimated).
  - Retrieval Precision (Jaccard similarity).
  - Retrieval Diversity (Inverse variance of similarity).
- **Procedure**:
  1. Initialize library with N skills.
  2. For each of 500 tasks:
     - Retrieve top-k=5 skills.
     - Execute solution path (if retrieved skills match ground truth).
     - Log metrics.
     - If task count % 10 == 0 and pruning enabled: Apply heuristic.
  3. Aggregate results per configuration.

### 3. Statistical Analysis (FR-005, FR-006, FR-007)

**Rationale**: To identify non-monotonic trends and validate the intervention.

**Methods**:
- **Piecewise Linear Regression (PLR)**:
  - Model: `SuccessRate ~ LibrarySize + Breakpoint + Interaction`.
  - Goal: Identify `x0` (tipping point) where slope changes significantly.
  - Tool: `pwlf` (Piecewise Linear Fit) or custom implementation in `scipy.optimize`.
- **Variance Inflation Factor (VIF)**:
  - Check collinearity between "Library Size" and "Total Redundancy".
  - Threshold: VIF < 5.0 (FR-007).
- **Hypothesis Testing**:
  - Paired t-test (or Wilcoxon signed-rank if non-normal) comparing Pruning vs. Non-Pruning success rates at high library sizes (50, 100).

## Compute Feasibility & Data Strategy

### CPU-First Approach
- **Embeddings**: `sentence-transformers` on CPU. 100 skills is negligible.
- **Agent Loop**: Pure Python logic. No heavy LLM inference; "execution" is simulated by checking ground-truth match.
- **Memory**: < 1 GB RAM required.
- **Time**: < 1 hour for full sweep.

### GPU Escape Hatch (Not Required)
- No GPU needed. The entire simulation is CPU-tractable. If a future iteration requires fine-tuning embeddings, the plan would shift to a Kaggle GPU kernel with 8-bit quantization, but this is not currently necessary.

### Data Availability
- **Synthetic**: Data is generated on-the-fly. No external download, no access-gated datasets.
- **Reproducibility**: Seeds are pinned. `generate_data.py` produces checksums.

## Decision Rationale

| Decision | Rationale | Alternative Rejected |
|----------|-----------|----------------------|
| Synthetic Data | Requires ground-truth solution paths impossible to guarantee in real code. | Real codebases (lack of ground truth). |
| CPU-Only | 100 skills is too small to justify GPU; CPU is faster for simple logic. | GPU acceleration (unnecessary overhead). |
| PLR for Tipping Point | Standard method for detecting threshold effects in non-linear data. | Logistic regression (less interpretable for "breakpoint"). |
| Jaccard for Precision | Directly measures set overlap (retrieved vs. ground truth). | Cosine similarity of sets (less standard for discrete skill sets). |

## Limitations

- **External Validity**: Results apply to the synthetic environment; generalization to real-world chaotic codebases is associative.
- **Skill Definition**: "Skills" are simulated Python functions; real-world code has dependencies and side effects not modeled.
- **Token Estimation**: Token usage is estimated based on function length, not actual LLM API calls.
