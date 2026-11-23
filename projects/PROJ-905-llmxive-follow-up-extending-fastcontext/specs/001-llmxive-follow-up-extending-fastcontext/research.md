# Research: FastContext-Lite (Deterministic Repository Explorer)

## Research Question
Does replacing the learned exploration subagent in FastContext with a deterministic, rule-augmented retrieval mechanism preserve token efficiency and context precision for code repositories with high structural regularity?

## Dataset Strategy

### Verified Datasets
This project relies on the **SWE-bench** dataset, which is available via Hugging Face.
- **Source**: `princeton-nlp/SWE-bench` (Verified via Hugging Face Datasets Hub).
- **Access Method**: Programmatic streaming via `datasets.load_dataset("princeton-nlp/SWE-bench", split="test", streaming=True)`.
- **Code Retrieval Mechanism**: The dataset provides `repo_id` and `base_commit`. The pipeline will perform a `git clone <repo_id>@<base_commit>` for each instance to retrieve the full code repository, as the dataset does not contain the full code snapshot directly.

*Note: The "FastContext" baseline model is not a downloadable dataset but a codebase/implementation. The "TF-IDF" datasets listed in the input block (Long Covid) are irrelevant to this code-repair task and are NOT used.*

### Data Acquisition & Processing
1. **Streaming**: The pipeline will stream SWE-bench instances to avoid memory overflow.
2. **Ground Truth Extraction**: Ground-truth relevant files are extracted from the `test_patch` and `instance` metadata in SWE-bench. This is independent of the structural heuristics used for scoring.
3. **Static Analysis**: A custom script (`static_analysis.py`) will compute the `regularity_score` for each repository.

### Dataset Variable Fit
- **Required**: Repository file structure (directory names, import patterns), Ground Truth files.
- **Available**: SWE-bench provides the `repo_id` and `base_commit` (via which the code is cloned), and task annotations.
- **Fit**: The dataset contains the necessary variables. No missing variables detected.

## Methodology

### 1. Structural Regularity Scoring (FR-001)
A composite score (0.0–1.0) will be calculated based on:
- **Directory Naming**: Consistency of standard directories (`src/`, `tests/`, `docs/`). **Mechanism**: `os.walk` or `pathlib` traversal of the file system to check for presence and naming conventions.
- **Test Placement**: Proximity of test files to source files. **Mechanism**: `pathlib` calculation of normalized relative path distance between `src/` and `tests/` directories (not AST traversal).
- **Import Patterns**: Adherence to standard import hierarchies. **Mechanism**: `ast.parse` to build an import graph, calculating graph density and average path length.
- **Weighting**: Weights will be determined by pilot validation (T027) but initially set to equal contribution.
- **Independence Verification**: Ground-truth relevant files are extracted *only* from `test_patch` and `instance_id`, ensuring no overlap with the structural heuristics used for scoring.
- **Operationalization Note**: "Structural Regularity" is operationalized as "adherence to standard packaging conventions" (syntactic), not semantic complexity.

### 2. Stratification (FR-002)
Repositories will be sorted by `regularity_score` using a **stable sort** (descending score, then ascending `instance_id` for tie-breaking) and split into:
- **Regular Set**: Top [deferred] of scores.
- **Irregular Set**: Bottom [deferred] of scores.
This ensures a balanced comparison as per US-1. A fixed random seed is used for any tie-breaking logic.

**Addressing Circular Validation**: The 'Regular' set is defined by structural heuristics, but the validation target (precision) is measured against *independent* ground-truth annotations. The hypothesis is about efficiency on regular structures, and the precision is measured against a ground truth that does not rely on the heuristics.

### 3. FastContext-Lite Engine (FR-003)
- **Mechanism**: Hybrid Retrieval (AST symbol resolution + TF-IDF).
- **Heuristics**: Rule-based search for `tests/`, `src/`, `main.py`.
- **Index**: `TfidfVectorizer` with `ngram_range=(1, 2)` and `max_features=10000`.
- **Execution**: CPU-only. Enforced via `torch.set_device('cpu')`, `os.environ['CUDA_VISIBLE_DEVICES']='-1'`, and a runtime assertion check.
- **Construct Validity**: The engine uses AST-based symbol resolution to identify candidate files, then applies TF-IDF *only* within that candidate set to rank them. This ensures TF-IDF operates on semantically relevant code, not raw text.

### 4. Baseline Execution (FR-004)
- **Model**: Original FastContext (large-scale parameter count).
- **Constraint**: Must run on CPU. If the model is too large for the 7GB RAM limit, the pipeline will use the **GPU Escape Hatch** (Kaggle) to run the 4B model at its theoretical limit.
- **Scientific Control**: The baseline will be run at its theoretical limit (no aggressive quantization if possible, or documented quantization).
- **Metrics**:
  - **Context Precision**: Calculated as Intersection over Union (IoU) of retrieved file paths vs. ground-truth file paths.
  - **Total Tokens**: Counted using the `tiktoken` library with the specific tokenizer used by the baseline model, summing tokens in the retrieved context.
  - **Latency**: Wall-clock latency is recorded for *every* repository processed.
- **Hardware Normalization**: Since the Baseline may run on GPU and Lite on CPU, raw wall-clock latency is not directly compared. Instead, we compare:
  - **Inference Efficiency**: Precision per Token.
  - **Hardware-Normalized Latency**: Latency scaled by theoretical FLOPS ratio (or reported separately with a disclaimer).

### 5. Statistical Analysis (FR-005, FR-006)
- **Pre-Stratification Power Check**: Calculate the minimum required N for the 'Regular' set *before* splitting. If the initial SWE-bench subset (n=1000) yields a 'Regular' set < 30, the study is underpowered, and results will be interpreted as exploratory or use bootstrapping.
- **Primary Test**: Paired t-test (or Wilcoxon signed-rank if normality fails) on the **"Regular" set** metrics (Precision, Tokens, Latency), pairing by `instance_id`.
- **Secondary Analysis**: **Segmented Regression** (Piecewise Linear Regression) of Performance Delta vs. Regularity Score to identify the boundary threshold. The model will use a breakpoint search algorithm (e.g., `pwlf` library) to find the sharp drop-off.
- **Power Target**: 0.80 (Source: Wikipedia, Power (statistics)).
- **Alpha**: [deferred] pending power analysis. Bonferroni correction will be applied to the final deferred threshold.
- **Measurement Validity**:
  - **Precision**: Validated against SWE-bench ground-truth annotations (independent of heuristics).
  - **Latency**: Measured via `time.perf_counter()`.
- **Addressing Mathematical Coupling**: The regression uses Performance Delta (a derived metric) against the Regularity Score. The 'boundary' is identified as the point where the *residuals* of the regression exceed a threshold, rather than a direct correlation of the score itself.
- **Performance Degradation (FR-006)**: Calculated as `(Baseline_Precision - Lite_Precision) / Baseline_Precision * 100` **specifically on the "Irregular" set**.
- **Threshold Confirmation**: The 10% precision drop threshold (SC-004) is used to confirm boundary conditions.

## Statistical Rigor & Feasibility

### Multiple Comparisons
If multiple metrics (Precision, Tokens, Latency) are tested, a **Bonferroni correction** will be applied to the *final* significance threshold ($\alpha_{final} = 0.05 / 3 \approx 0.017$) to control family-wise error rate.

### Sample Size & Power
- **Power Target**: 0.80.
- **Alpha**: [deferred].
- **Limitation**: If the stratified "Regular" set contains fewer than 30 repositories, the power analysis will be reported as "underpowered," and results will be interpreted as exploratory.

### Causal Inference
This is an **observational** study (we observe the effect of structure on performance). Claims will be framed as **associational**. No randomization of repository structure is performed; thus, causal claims about "structure causing efficiency" are not licensed.

### Compute Feasibility
- **CPU-First**: All methods (TF-IDF, static analysis, t-tests) are CPU-tractable.
- **GPU Escape Hatch**: The baseline FastContext model *may* require GPU for reasonable speed. If the CPU run is infeasible (>6h or OOM), the plan will switch to a **quantized 8-bit** version on the **Kaggle GPU escape hatch**. This is the *only* GPU usage, strictly for the baseline comparison to ensure valid latency metrics, while FastContext-Lite remains CPU-only. The comparison will be normalized for hardware.

## Decision Rationale
- **Why CPU-first?** The project goal is edge deployment; results must reflect CPU performance.
- **Why TF-IDF?** It is a standard, deterministic, and lightweight retrieval method suitable for code.
- **Why Stratification?** The hypothesis specifically targets "structural regularity." A random split would dilute the signal.
- **Why SWE-bench?** It is the only verified, open dataset with task-level ground truth for code repair.
- **Why Normalized Latency?** To isolate the subagent effect from hardware speedups when comparing CPU vs. GPU runs.