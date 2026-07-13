# Research: llmXive Follow-up: Input Noise Injection for Latent Separability

## 1. Research Question & Hypothesis

**Question**: Does injecting controlled noise into the input embedding manifold of a frozen LLM increase the separability of latent "thought" vectors for distinct questions of the same task type, without breaking semantic validity?

**Hypothesis**: The current representational collapse (low separability) is caused by the smoothness of the input manifold. Injecting noise ($\sigma$) and projecting to the nearest valid token will push inputs into regions of the manifold where the model's internal representations are more distinct (higher separability), provided the noise does not exceed the "validity collapse point."

**Reframing**: Due to the discrete nature of tokenized models, the hypothesis is reframed from "continuous manifold smoothness" to **"discrete input neighborhood robustness"**. The experiment measures the sensitivity of the latent representation to small, semantically valid token substitutions.

## 2. Dataset Strategy

The experiment relies on reasoning tasks from the **BigBench** suite. The official BigBench data is hosted under `google-research-datasets/big_bench` or via the `bigbench` Python package.

| Dataset Component | Source/URL | Usage | Verification |
| :--- | :--- | :--- | :--- |
| **BigBench Core** | `google-research-datasets/big_bench` (HuggingFace) | Source of reasoning tasks; provides `input` and `expected_answer`. | Verified via `bigbench` Python package. |
| **Task Generation** | Dynamic generation via `bigbench` package | Generates "within-task" pairs by sampling distinct questions from the same task type. | No pre-computed "failing pairs" exist; pairs are generated dynamically. |
| **External Embedding Model** | `sentence-transformers/all-MiniLM-L6-v2` (HuggingFace Hub) | Computes input semantic drift (FR-009). | Pre-trained, CPU-compatible, no GPU required. |
| **BERTScore** | `pip install bertscore` | Computes output semantic validity (FR-006). | No specific URL; installed via PyPI. |

**Data Availability Note**: The spec assumes a "23 reasoning tasks" dataset. The implementation will load the available BigBench tasks via the `bigbench` package and dynamically generate "within-task" pairs (questions sharing the same task label/type). If the specific "23 tasks" list is not fully represented in the available BigBench subsets, the system will process the available verified subsets and report the coverage gap, rather than fabricating a dataset.

## 3. Methodology

### 3.1. Model Selection & Setup
- **Model**: `TinyLlama/TinyLlama-1.1B-Chat-v1.0` (Verified CPU-tractable variant).
- **Constraint**: Must run on 2 CPU cores, 7GB RAM.
- **Strategy**:
  - `TinyLlama-1.1B` is selected over Llama-3-8B to guarantee CPU feasibility on 7GB RAM.
  - **Justification**: The research question is about the *mechanism* of manifold smoothness, which is present in smaller models. The relative effect (separability increase) is the metric, not the absolute performance of a specific 8B model.
  - **Loading**: `model.eval()`, `torch.no_grad()`, `device="cpu"`, `torch_dtype=torch.float32` (or `float16` if memory allows, but `float32` is safer for CPU stability).
  - **Fallback**: `google/gemma-2b` if memory constraints persist.

### 3.2. Perturbation Algorithm (FR-003)
1. **Tokenization**: Convert input text to token IDs.
2. **Embedding Lookup**: Retrieve continuous embedding vectors $E \in \mathbb{R}^{d}$ for each token.
3. **Noise Injection**: Add Gaussian noise $N \sim \mathcal{N}(0, \sigma^2)$ to $E$.
4. **Projection**: Project noisy vector $E' = E + N$ to the nearest valid token embedding in the model's vocabulary (minimizing Euclidean distance).
5. **Forward Pass**: Use the projected token IDs for inference.
6. **Sweep**: Iterate $\sigma$ from 0.01 to 0.20 in steps of 0.01.
7. **Verification**: Measure the actual Euclidean distance between the baseline token embeddings and the projected token embeddings to ensure a monotonic relationship with $\sigma$. If non-monotonic, group results by "actual perturbation magnitude".

### 3.3. Validity Checks
- **Input Validity (FR-009)**: Compute cosine similarity between baseline input embedding (SBERT) and perturbed input embedding (SBERT). Threshold $\ge 0.95$.
- **Output Validity (FR-006)**:
  1. **Exact Match**: Compare generated answer tokens to `expected_answer`.
  2. **Semantic Match**: BERTScore (F1) $\ge 0.85$.
  3. **Perplexity**: Output perplexity $\le 2.0 \times$ baseline perplexity.
- **Filtering**: Pairs failing any check are excluded from the statistical analysis.
- **Validation Subset**: A small, fixed subset of 10 pairs per task type is reserved for perplexity validation (Constitution Principle VI), distinct from the test pairs.

### 3.4. Statistical Analysis (FR-005, SC-001)
1. **Metric**: Pairwise cosine similarity of latent "thought" vectors (baseline vs. perturbed) for distinct questions within the same task type.
2. **Unit of Analysis**: The distribution of pairwise similarities.
   - Baseline: Distribution of Sim(Q1, Q2) for all pairs.
   - Perturbed: Distribution of Sim(Q1', Q2') for all pairs (where Q1' and Q2' are independently perturbed).
3. **Test**:
   - Check normality (Shapiro-Wilk).
   - If normal and $n \ge 30$: Paired t-test (comparing the two distributions of similarities).
   - Else: Wilcoxon signed-rank test or Kolmogorov-Smirnov test (if distributions are compared directly).
4. **Correction**: Apply Bonferroni or Holm correction for multiple comparisons (across $\sigma$ levels and task types).
5. **Power Analysis**:
   - With multiple task types and sigma levels, the multiple comparison burden is high (hundreds of tests).
 - n=50-100 pairs is a pragmatic minimum for the Wilcoxon test to detect medium effect sizes (d=0.5) with [deferred] power after Bonferroni correction.
   - If power is insufficient, the plan will report the effect size and confidence interval without claiming significance, or aggregate across task types if homogeneity is found.
6. **Outcome**: Report p-value, effect size (Cohen's d or rank-biserial), and confidence interval.

### 3.5. Computational Feasibility (SC-004)
- **Memory**: Use batch processing (e.g., 1-4 samples per batch) to keep RSS < 7GB.
- **Time**: The sweep (20 steps) $\times$ pairs is computationally heavy.
  - **Optimization**: Limit the number of pairs per task type to a statistically significant sample (e.g., 50-100 pairs) if the full dataset is too large, ensuring $n \ge 30$ for parametric tests.
  - **Parallelization**: Not possible on 2 cores efficiently for deep learning; rely on optimized CPU kernels (MKL/OpenBLAS).
  - **Fallback**: If runtime > 4h, reduce the $\sigma$ sweep range or step size (e.g., 0.05 steps) and document the trade-off.

## 4. Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Model OOM** | Job fails, no results. | Default to smaller model (TinyLlama); implement aggressive batch sizing; monitor RSS via `tracemalloc`. |
| **No Valid $\sigma$** | Inconclusive result. | Report the full trade-off curve (validity vs. perturbation); flag as "No sweet spot found." |
| **Semantic Collapse** | Model outputs gibberish. | Strict validity gates (FR-006, FR-009) will exclude these; report the "collapse point." |
| **Statistical Power** | Low $n$ after filtering. | Use Wilcoxon test; report reduced power; aggregate across task types if appropriate. |
| **CPU Speed** | Runtime > 6h. | Limit pairs per task; reduce sweep steps; use optimized CPU libraries. |

## 5. Decision Log

- **Model Choice**: `TinyLlama-1.1B` selected over Llama-3-8B to guarantee CPU feasibility on 7GB RAM. Rationale: The phenomenon (manifold smoothness) is architectural, not scale-dependent in this context.
- **Validity Threshold**: SBERT $\ge 0.95$ chosen to ensure "small" perturbations; BERTScore $\ge 0.85$ for semantic preservation.
- **Statistical Test**: Wilcoxon default if $n < 30$ or non-normal, ensuring robustness without parametric assumptions.
- **Hypothesis Reframing**: "Discrete input neighborhood robustness" instead of "continuous manifold smoothness" to align with the tokenized nature of the model.
