# Research: llmXive follow-up: extending "LatentSkill: From In-Context Textual Skills to In-Weight Latent Skills"

## Research Question

Can the latent space of LoRA adapters be approximated via simple vector retrieval and arithmetic interpolation on a CPU, effectively replacing the computationally expensive hypernetwork while maintaining performance within an acceptable degradation threshold?

## Dataset Strategy

**Primary Data Source**: The project requires the pre-trained LoRA (A and B) matrices and task descriptions from the original "LatentSkill" study.

> **CRITICAL NOTE**: The following dataset references are **placeholders**. The implementation MUST only proceed if the "Verified datasets" block provided at runtime contains a valid, reachable URL for the LoRA weights. If no verified source exists, the project must state "No open source data available for LatentSkill LoRA weights" and **halt**.

| Dataset Name | Description | Verified URL / Loader | Status |
| :--- | :--- | :--- | :--- |
| **LatentSkill LoRA Weights** | Pre-trained A and B matrices for ALFWorld and Search-QA benchmarks. | `See Verified Datasets Block` | **Pending Verification** |
| **Sentence-Transformers** | Frozen model for text embeddings (`all-MiniLM-L6-v2`). | `sentence-transformers/all-MiniLM-L6-v2` (HuggingFace) | **Available** |
| **Composite Task Descriptions** | Text descriptions of novel tasks (generated or held-out). | Generated via spec-defined combination logic using ALFWorld/Search-QA environments. | **Available** |
| **Composite Validation Subset (CVS)** | A [deferred] split of the original dataset with ground-truth weights for known composite tasks (used for FR-007/SC-005). | Subset of the primary dataset (if available). | **Conditional** |

**Data Acquisition Plan**:
1.  **Download**: Use `datasets.load_dataset()` or `huggingface_hub` to fetch the LoRA weights if a verified HF dataset ID exists. If a direct URL is provided, use `wget`/`requests` with checksum validation.
2.  **Validation**: Verify file integrity (SHA256) against the manifest.
3.  **Processing**: Flatten A and B matrices into a single vector per task. Normalize to unit length.
4.  **Streaming**: If the dataset exceeds a substantial size threshold, stream the weights in chunks to compute aggregate statistics without loading the full index into RAM.

**Dataset Feasibility Check**:
- **Variable Fit**: The study requires *task descriptions* and *weight matrices*. The dataset must contain both. If the dataset only contains weights without descriptions, the retrieval mechanism (FR-002) cannot function.
- **Access**: If the dataset requires a token (e.g., gated HF repo), the CI runner cannot access it. The plan must fail gracefully or switch to a public proxy dataset if available (none currently verified).
- **Fallback**: If the primary dataset is unavailable, the project **halts**. No open substitute exists for the specific A/B matrices required.

## Methodology & Statistical Rigor

### 1. Vector Construction (FR-001)
- **Method**: Load LoRA A (down-projection) and B (up-projection) matrices. Concatenate and flatten.
- **Normalization**: L2 normalization to ensure cosine similarity is valid.
- **Dimensionality**: $D = \sum (r \times d_{in} + d_{out} \times r)$ per adapter.

### 2. Retrieval Strategies (FR-003)
- **Query Generation**: Use `all-MiniLM-L6-v2` (frozen, CPU) to embed task descriptions.
- **Strategy A (Nearest Neighbor)**: Retrieve the single vector with max cosine similarity.
- **Strategy B (Arithmetic Mean)**: Average top-$k$ vectors (unweighted).
- **Strategy C (Cosine-Weighted)**: Weighted average where $w_i \propto \cos(query, v_i)$.
- **Baseline**: **Primary**: Original LatentSkill hypernetwork inference. **Fallback**: If unavailable, a standard fine-tuned adapter per task is used as a proxy, with the report explicitly noting this limitation.

### 3. Evaluation & Validation (FR-004, FR-007, SC-005)

#### 3.1 Primary Validity Check: Local Linearity (SC-005)
- **Method**: For the **Composite Validation Subset (CVS)** (a [deferred] split of the dataset with ground-truth weights), calculate the cosine distance between the synthesized weights (via retrieval/interpolation) and the **ground-truth weights**.
- **Threshold**: If the error rate exceeds **0.05**, the latent space is deemed non-linear for this purpose.
- **Fallback**: If the CVS does not exist (no ground-truth weights for composites), SC-005 is redefined to measure **Functional Linearity**: the success rate improvement of the retrieval strategy over a zero-shot baseline.

#### 3.2 Secondary Validity Check: Global Text-Weight Alignment (FR-007)
- **Method**: Calculate Pearson correlation between text-space cosine distances and weight-space cosine distances for the **held-out set of known task pairs** (from the CVS).
- **Constraint**: The weight-space distance must be calculated against **ground-truth weights**, not synthesized weights, to avoid circularity.
- **Interpretation**: A high correlation supports the hypothesis, but the primary validity check remains the local linearity test (3.1).

#### 3.3 Success Metric & Control (FR-004, FR-008)
- **Success Metric**: Binary outcome (0/1) from environment logic (ALFWorld/Search-QA).
- **Zero-Shot Control**: Run tasks with **no adapter** to establish a baseline success rate ($S_{zero-shot}$).
- **Adapter Gain**: Calculate $Gain = S_{adapter} - S_{zero-shot}$ to isolate the adapter's contribution from the base model's stochasticity and capability ceiling.
- **Stability**: Run each task $N$ times. Start with $N=5$. Iterate until the 95% confidence interval width of the success rate is < 0.1 or $N=20$ is reached.

### 4. Statistical Testing (FR-005, FR-006)
- **Tests**: **Primary**: McNemar's test for paired binary data (comparing success rates of strategies vs. baseline). **Secondary**: Paired t-test or Wilcoxon signed-rank (if normality of proportions holds, requiring large N).
- **Multiple Comparisons**: Apply **Benjamini-Hochberg (BH)** procedure to control False Discovery Rate (FDR) across the **combined set of 12 tests** (3 strategies x 4 k-values: k=1, 3, 5, 10) for each primary comparison.
- **Power Analysis**: Target power = 0.8, minimum detectable effect size (Cohen's h) = 0.2. This requires a minimum of **N=30** composite tasks. If N < 30, the study is powered only to detect large effects (h >= 0.5), and negative results will be qualified by this limitation.

### 5. Compute Feasibility (CPU-First)
- **Memory**: Flattened vectors for ~500 adapters (assuming $r=8$, $d=4096$) will be ~10-20 MB, well within RAM limits.
- **Latency**: `all-MiniLM-L6-v2` runs in <100ms on CPU. Vector search (scikit-learn `NearestNeighbors`) is negligible for this scale.
- **GPU Escape Hatch**: Not required for this specific pipeline (retrieval + evaluation on small scale). If the base LLM evaluation exceeds RAM, the plan will use a smaller quantized model or a sampled subset of tasks.

## Decision Rationale

| Decision | Rationale |
| :--- | :--- |
| **CPU-Only Execution** | The spec targets edge/serverless deployment. Running on CPU validates the primary hypothesis. GPU is not needed for vector math on this scale. |
| **No Synthetic Ground Truth** | Generating "true weights" for novel tasks is scientifically impossible without re-training. The plan relies on *environment success* as the ground truth, avoiding fabrication. |
| **Benjamini-Hochberg Correction** | Required by FR-006 to prevent false positives when testing multiple strategies and sensitivity parameters. Applied to the full set of 12 tests. |
| **Frozen Sentence-Transformer** | `all-MiniLM-L6-v2` is small, CPU-efficient, and standard for semantic retrieval, ensuring reproducibility. |
| **McNemar's Test** | Preferred over t-test for paired binary data to address independence and distribution assumptions. |
| **Functional Linearity Fallback** | If ground-truth weights for composites are absent, the plan uses success rate as the primary linearity metric, proposing a constitutional amendment to accept this. |

