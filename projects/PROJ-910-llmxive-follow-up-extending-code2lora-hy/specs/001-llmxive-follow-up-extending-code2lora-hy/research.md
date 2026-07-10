# Research: llmXive follow-up: extending "Code2LoRA: Hypernetwork-Generated Adapters for Code Language Models under Software Evolution"

## 1. Problem Statement & Hypothesis

**Problem**: The original CodeLoRA framework relies on a parameter-scale neural encoder to generate repository-specific LoRA adapters. This introduces significant latency and memory overhead, making it infeasible for standard CI/CD environments (e.g., GitHub Actions free tier).

**Hypothesis**: Syntactic features extracted via static analysis (AST) are sufficient to generate high-quality LoRA adapters for code evolution tasks, achieving >80% of the baseline neural encoder's accuracy with at least one order of magnitude lower generation latency, **when compared on identical CPU hardware**.

## 2. Dataset Strategy

The project utilizes the **RepoPeftBench** dataset, specifically the Python subset for assertion-completion tasks.

| Dataset | Source URL | Usage | Verification |
|---------|------------|-------|--------------|
| RepoPeftBench (Python Subset) | https://huggingface.co/datasets/code2lora/repopeftbench-ood/resolve/main/commits/ood_test.parquet | Primary test set for adapter evaluation (FR-004, US-2). | Verified via HuggingFace `datasets` library. |

**Dataset Fit Analysis**:
- **Required Variables**: The study requires repository source code (Python files) and associated test assertions (for evaluation).
- **Available Variables**: The verified dataset provides commits with source code and test cases (assertions).
- **Fit Confirmation**: The dataset contains the necessary source code for AST feature extraction and the ground-truth assertions for exact-match evaluation. No missing variables detected.

**Data Loading Strategy**:
- Use `datasets.load_dataset("parquet", data_files=URL)` to fetch the parquet file.
- Subset to Python files only (filter by extension).
- Cache locally in `data/raw/` with checksum verification (Constitution Principle III).
- **Split Strategy**: Data is split into **Training Set ([deferred])** for MLP training and **Test Set ([deferred])** for final evaluation to prevent circular validation.

## 3. Methodology & Statistical Rigor

### 3.1 Feature Extraction (FR-001)
- **Method**: Python `ast` and `tokenize` modules.
- **Metrics**:
  - Cyclomatic Complexity (McCabe)
  - Depth of Inheritance Tree (DIT)
  - Import Graph Degree Centrality (using `networkx` on import statements)
  - Token Histograms (frequency of token types)
- **Handling Edge Cases**:
  - **AST Parser Failure**: If `ast.parse()` raises `SyntaxError`, log warning with filename (FR-007) and skip file.
  - **Memory Overflow**: Monitor RAM usage; abort if >6 GB (FR-008).
  - **Incompatible Checkpoint**: Validate base model architecture before loading (FR-009).

#### 3.1.1 Semantic Control Baseline
To distinguish "syntactic sufficiency" from "semantic failure", we will train a **Linear Probe** on raw token embeddings (frozen base model) to predict the task output. This establishes a semantic baseline. The AST-MLP performance will be compared against this probe to quantify the loss of semantic information.

### 3.2 Adapter Generation (FR-002, FR-003)
- **Architecture**: Replace neural encoder with a 3-layer MLP (ReLU activations) mapping AST feature vectors (fixed length) to the base model's embedding dimension.
- **Training**:
  - **Objective**: Minimize cross-entropy loss on the **Training Set** to predict **LoRA Adapter Weights**.
  - **Constraint**: Run on CPU only. Use `torch.float16` for the base model weights to save RAM.
  - **Memory Strategy**: Load the base model (TinyLlama-1.1B) in `float16` (approx 2.2GB). Process data in small batches. **Do not load GGUF and float16 simultaneously.** Use GGUF only for the final inference phase.
  - **Validation**: Evaluate on the **held-out Test Set** only. This prevents circular validation where the MLP is trained and tested on the same data.

### 3.3 Evaluation (FR-004, US-2)
- **Metric**: Exact-match score on assertion-completion tasks (Test Set only).
- **Baseline Comparison**:
  - **Protocol**: Re-run the Code2LoRA pipeline on the **same CPU runner** using a **frozen, small neural encoder** (not the 0.6B model) to generate embeddings.
  - **Architecture**: The baseline MLP uses the **same architecture** as the AST-MLP but receives neural embeddings as input. Both MLPs output **LoRA Adapter Weights**.
  - **Fairness**: This ensures the comparison isolates the feature type (AST vs. Neural) and not the architecture or hardware.
- **Statistical Test**:
  - **Primary**: **Paired t-test** (per Constitution Principle VII) comparing exact-match scores of AST-adapter vs. Neural-adapter on the same test samples.
  - **Secondary**: Wilcoxon signed-rank test if normality assumptions (Shapiro-Wilk) are violated.
  - **Power Analysis**: With N=20 repositories, the Minimum Detectable Effect Size (MDES) at 80% power and alpha=0.05 is approx 0.65. Results will be framed as "exploratory" if the observed effect is smaller than MDES.
- **Latency Measurement**: Record adapter generation time (start to finish) and inference latency (ms per sample) on the same CPU hardware.

### 3.4 Sensitivity Analysis (FR-005, US-3)
- **Method**: Iteratively remove feature subsets (e.g., only token counts, then add cyclomatic complexity, then full AST graph).
- **Collinearity Handling**: Before analysis, features are standardized. The MLP uses **L2 regularization** to mitigate the impact of collinear features. The sensitivity analysis reports the performance drop when features are removed *with* this regularization active.
- **Output**: Sensitivity curve (Accuracy vs. Feature Complexity).
- **Threshold**: Identify minimal feature set achieving >80% of baseline accuracy (SC-003).

### 3.5 Statistical Rigor & Limitations
- **Multiple Comparisons**: If multiple sensitivity subsets are tested, apply Bonferroni correction to p-values.
- **Power Justification**: Acknowledged limitation: N=20 is small. MDES is calculated and reported.
- **Causal Claims**: Claims are framed as associational (performance correlation with feature complexity).
- **Collinearity**: Descriptive statistics on collinearity reported; L2 regularization applied.

## 4. Compute Feasibility Plan

- **Environment**: GitHub Actions free-tier (2 CPU, 7 GB RAM, 6h timeout).
- **Model Strategy**:
  - **Primary Target**: **TinyLlama-1.1B**.
  - **Training**: Load in `float16` (~2.2 GB). Use batched processing to keep total RAM < 6 GB (OS + Model + Hypernetwork + Overhead).
  - **Inference**: Use `llama-cpp-python` with **GGUF 4-bit** format (~600-800 MB) to minimize memory during evaluation. **Never load both formats simultaneously.**
  - **Fallback**: If OOM occurs on TinyLlama-1.1B, fallback to **CodeLlama-1.3B** (if smaller footprint) or reduce batch size further. **Phi-2 (2.7B) is explicitly excluded** as it violates the 1.5B constraint.
  - **Trigger**: Fallback is triggered by `MemoryError` or explicit RAM monitoring > 6.5 GB.
- **Libraries**: Pin `torch` to CPU-only wheels. Avoid `bitsandbytes`.
- **Runtime**: Parallelize feature extraction across files (but not models) to maximize CPU usage without exceeding RAM.

## 5. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Base model too large for 7GB RAM | Project fails | Use TinyLlama-1.1B (1.1B); fallback to CodeLlama-1.3B; batched training. |
| AST features insufficient for semantic tasks | Low accuracy | Sensitivity analysis identifies gap; report failure modes; compare against semantic control probe. |
| Runtime > 6 hours | CI failure | Aggressive sampling; optimize feature extraction (streaming). |
| Non-Python files in dataset | Parsing errors | Filter by `.py` extension; log skipped files. |
| Memory Conflict (GGUF vs Float16) | OOM | Strict protocol: Float16 for training, GGUF for inference. Never both. |