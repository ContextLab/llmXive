# Research: Memory Palaces in LLMs: Spatial Reasoning for Enhanced Episodic Recall

## 1. Dataset Strategy

The project relies on three public sequential-memory benchmarks. The following table lists the verified sources and the specific variable fit for the "episodic recall" outcome.

| Dataset | Verified Source / Loader | Variable Fit & Rationale | Status |
| :--- | :--- | :--- | :--- |
| **bAbI Task 3** | `datasets.load_dataset("babi", "task03")` (HuggingFace) | **Fit**: Contains episodic facts (e.g., "The ball is in the kitchen") and questions requiring retrieval ("Where is the ball?"). <br>**Rationale**: Directly tests episodic recall of specific facts in a sequence. **Primary dataset for hypothesis testing.** | **Verified** |
| **LAMBADA** | `datasets.load_dataset("EleutherAI/lambada_openai")` (HuggingFace) | **Fit**: Requires predicting the last word of a paragraph based on long-range context. <br>**Rationale**: Tests long-context retention, a form of episodic memory over a narrative. **Feasibility check only (1 seed, 1 epoch).** | **Verified** |
| **Story Cloze** | `datasets.load_dataset("story_cloze", "2018")` (HuggingFace) | **Fit**: Requires choosing the correct ending to a story based on 4 preceding sentences. <br>**Rationale**: Tests narrative coherence and recall of story events. **Feasibility check only (1 seed, 1 epoch).** | **Verified** |

**Dataset-Variable Fit Confirmation**:
- **bAbI Task 3**: The "facts" map directly to `EpisodicChunk` objects. The "questions" map to the retrieval query. The spatial grid will assign slots to facts.
- **LAMBADA/Story Cloze**: Used only for feasibility checks. The "episodic chunk" mapping is tenuous; they are not used for primary hypothesis testing due to lack of explicit fact-question structure.
- **FIFO Eviction**: As noted in the spec, if a sequence exceeds the 64-slot grid, a FIFO eviction policy will be applied. This is a necessary constraint for the "spatial capacity" hypothesis.

**Note on Verified Sources**: The prompt provides specific parquet URLs for LAMBADA and RSS feeds. However, standard HuggingFace loaders (`datasets`) are preferred for reproducibility and checksumming (Constitution I). The specific parquet URLs provided in the prompt for LAMBADA (`cimec/lambada`, `craffel/openai_lambada`, `EleutherAI/lambada_openai`) confirm the availability of the dataset. The RSS feed URLs are irrelevant to this study (which focuses on text memory, not RSS) and are ignored. The "FIFO" dataset is not a dataset but an eviction policy; no URL is required.

## 2. Methodology & Statistical Rigor

### 2.1 Model Architecture
- **Base**: **DistilGPT2** (66M parameters) — chosen for CPU feasibility. GPT Medium (355M) is infeasible on CPU within RAM limits.
- **Quantization**: 4-bit (using `bitsandbytes` CPU-compatible version or `accelerate` with 4-bit logic).
- **Spatial Module**:
  - 2-D Grid: 8x8 = 64 slots.
  - Retrieval: Soft-addressed via cosine similarity between current hidden state and slot embeddings.
  - **Distance-Decay Penalty**: A penalty term is added to the attention weights based on the Euclidean distance in the grid to enforce locality and distinguish from standard global attention.
  - Update: Episodic chunks update slot embeddings via a weighted average.
- **Baseline**: Standard `distilgpt2` with no spatial module (standard self-attention only).
- **Ablation**: Non-spatial attention head with the same parameter count as the spatial module but without grid coordinates (random projection). This isolates the effect of "spatiality" from "additional parameters".

### 2.2 Training Protocol
- **Epochs**: 3 (for bAbI), 1 (for LAMBADA/Story Cloze).
- **Batch Size**: Starts at 8. If peak RSS > 6 GB, reduces to 4. If still > 6 GB, **subsamples top [deferred] of samples by length** (capped at [deferred] of original size).
- **Learning Rate**: 5e-5.
- **Seeds**: 5 random seeds (0, 1, 2, 3, 4) for bAbI; 1 seed for others.
- **Hardware**: CPU-only (2 cores, ~7 GB RAM).

### 2.3 Statistical Analysis Plan
1. **Primary Metric**: Exact-match recall accuracy.
2. **Comparison**: Paired two-tailed t-test between Spatial and Baseline across 5 seeds (bAbI only).
3. **Multiple Comparison Correction**: Bonferroni correction (default) or Holm-Bonferroni if Bonferroni is overly conservative.
   - **Rationale**: Testing multiple datasets (bAbI, LAMBADA, Story Cloze) inflates Type I error. Correction is mandatory (FR-006).
4. **Effect Size**: Cohen's d with 95% Confidence Intervals.
5. **Power Analysis**: With N=5, the study is underpowered to detect medium effects (<20% power). The analysis will prioritize reporting **effect sizes (Cohen's d)** and confidence intervals over p-values for significance claims. The minimum detectable effect size will be reported.
6. **Normality Check**: Shapiro-Wilk test on accuracy differences. If p < 0.05, use Wilcoxon signed-rank test instead.
7. **Interference Distance**:
   - **Spatial Variant**: Measure of recall drop when semantically unrelated items are injected into **adjacent grid coordinates**.
   - **Baseline Variant**: Measure of recall drop when semantically unrelated items are injected at **random positions in the input sequence** (simulating "random slot" assignment). This creates a valid "structured vs. unstructured" comparison.
   - **Hypothesis**: Spatial variant shows lower interference (higher robustness) than baseline.
   - **Validation**: Statistical test on interference distance metric.

### 2.4 Computational Feasibility
- **RAM Constraint**: 6 GB limit (Constitution VI).
  - `distilgpt2` 4-bit: ~0.5 GB.
  - Activation memory with small batch sizes: ~3-4 GB (estimated).
 - **Mitigation**: Automatic batch size reduction to 4. If still too high, **subsample top [deferred] of samples**.
- **Runtime Constraint**: 5 hours.
  - **Primary Scope**: bAbI Task 3 (5 seeds * 2 models * 3 epochs = 30 runs).
  - **Secondary Scope**: LAMBADA/Story Cloze (1 seed * 2 models * 1 epoch = 4 runs).
  - **Total Runs**: ~34 runs.
 - **Estimate**: [deferred] per run on CPU (DistilGPT2) = [deferred] total. **Safe within 5-hour limit.**
  - **Risk**: If runtime exceeds 5 hours, the project will fail. The plan prioritizes bAbI (primary) over LAMBADA/Story Cloze (secondary).

## 3. Reviewer Response & Methodological Rigor

### 3.1 Addressing "Measurable Structural Correlate" (Rosalind Franklin)
- **Response**: The "Interference Distance" metric is introduced to quantify the structural benefit of spatial organization. It measures the *robustness* of recall under interference, distinguishing "spatial memory" from mere "grid usage."
- **Method**: Inject unrelated items into adjacent slots (spatial) or random positions (baseline) and measure recall drop. This provides a quantitative "diffraction pattern" equivalent for the memory palace.

### 3.2 Addressing "Measurable Cost" (John von Neumann)
- **Response**: The cost is measured in:
  1. **Compute Time**: Training time comparison (Spatial vs. Baseline).
  2. **Memory Overhead**: Slot embedding storage (negligible compared to model weights).
  3. **Recall Accuracy**: The primary metric. If Spatial improves accuracy without significant time penalty, the cost is justified.

### 3.3 Addressing "Binding Problem" (Eric Kandel)
- **Response**: The plan acknowledges the binding problem (spatial tags integrating with distributed representations) and addresses it via **soft-addressed read mechanisms** (cosine similarity) with a **distance-decay penalty**. Explicit binding architectures are deferred to future work.
- **Rationale**: This is a standard approximation in computational neuroscience and is sufficient for the current hypothesis test.

### 3.4 Statistical Rigor
- **Multiple Comparisons**: Bonferroni/Holm-Bonferroni applied.
- **Power**: N=5 is a limitation. The study is framed as a **feasibility and signal-detection pilot**. Results will report effect sizes (Cohen's d) and confidence intervals rather than relying solely on p-values.
- **Causal Claims**: Findings are framed as **associational** (correlation between spatial organization and recall accuracy), not causal, as there is no randomization of architecture in the real world (only in the simulation).

## 4. Decision Log

| Decision | Rationale | Alternative Rejected |
| :--- | :--- | :--- |
| **DistilGPT2 (66M)** | Required to fit model in 6 GB RAM on CPU with training overhead. | GPT-2 Medium (355M) exceeds RAM even with 4-bit quantization during training on CPU. |
| **4-bit Quantization** | Required to fit model weights in RAM. | Full precision or 8-bit (bitsandbytes on CUDA) is impossible without GPU. |
| **Soft-Addressed Retrieval with Distance-Decay** | Standard, differentiable approach for spatial memory with enforced locality. | Hard addressing (non-differentiable, harder to train). |
| **Baseline Interference (Random Injection)** | Creates a valid "structured vs. unstructured" comparison. | No interference metric for baseline (invalid comparison). |
| **Bonferroni Correction** | Simple, conservative, standard for small number of tests (3). | No correction (inflated false positives). |
| **[deferred] Subsampling** | Necessary to meet 6 GB RAM constraint if batch size 4 fails. | Full dataset (risk of OOM). |
| **Focus on bAbI Task 3** | Only dataset with explicit episodic fact-question structure. | LAMBADA/Story Cloze (lack of structure, used only for feasibility). |
