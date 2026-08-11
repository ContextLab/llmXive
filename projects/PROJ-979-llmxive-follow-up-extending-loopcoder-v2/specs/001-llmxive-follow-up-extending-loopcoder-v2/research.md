# Research: llmXive follow-up: extending "LoopCoder-v2"

## Research Question

Does the initial semantic uncertainty (entropy) of a hidden state in an iterative refinement model predict its convergence trajectory on complex code generation tasks?

## Hypothesis

**H1**: Higher initial semantic entropy correlates with a later convergence step (or failure to converge), indicating a disconnect between internal confidence and reasoning capability.
**H0**: No correlation exists between initial entropy and convergence trajectory ($\rho = 0$).

## Dataset Strategy

The study utilizes two open, programmatic datasets for code generation. These are verified as directly downloadable via HuggingFace `datasets` library, satisfying the "open, directly-downloadable" constraint.

| Dataset | Purpose | Source / Loader | Verification |
|:--- |:--- |:--- |:--- |
| **HumanEval** | Primary benchmark for convergence and entropy extraction. Contains a collection of problems with reference solutions. | `datasets.load_dataset("openai/openai_humaneval")` | Verified URL: ` |
| **MBPP** | Secondary benchmark for robustness and generalization. | `datasets.load_dataset("Muennighoff/mbpp")` | Verified URL: ` |

**Dataset-variable fit**:
- **Required Variables**: Problem prompt, reference solution (ground truth), difficulty strata (baseline pass rates).
- **Fit Confirmation**: Both datasets provide prompts and reference solutions. Difficulty strata will be derived from baseline pass@1 rates reported in literature (HumanEval/MBPP original papers), not from the dataset itself, to ensure fixed a priori bins.
- **Access**: Both datasets are open and do not require credentials.

## Methodological Rigor

### 1. Semantic Entropy Extraction (FR-001)
- **Method**: For each problem, generate $N=10$ samples using `CodeLlama-7b-Instruct-hf`.
- **Clustering**: Cluster samples by **AST normalization and structural hashing ONLY**. **Strictly excludes** the benchmark's test suite used for convergence to prevent circular validation (Constitution Principle VI). "Functional equivalence" is NOT used for clustering; only syntactic structure.
- **Metric**: Shannon entropy over cluster probabilities.
- **Independence**: The clustering is based on the distribution of generated samples, not their proximity to the ground truth. This ensures the entropy metric is independent of the convergence outcome.
- **Edge Case Handling**: If entropy is undefined (deterministic output), assign minimal non-zero entropy or exclude (documenting rate).

### 2. Convergence Trajectory (FR-002, FR-003)
- **Method**: Run iterative refinement for $k \in \{, 2, 3\}$.
- **Metric**: First $k$ where output matches reference solution (via test suite).
- **Censoring**: If no convergence at $k_{max}=3$, treat as censored data.
- **Censoring Assumption Justification**: The survival analysis assumes non-informative censoring. We will test this by comparing the entropy distribution of censored vs. uncensored items. If distributions differ significantly, the results will be framed as a lower-bound estimate.
- **Analysis**: Spearman rank correlation with entropy. Use Kaplan-Meier estimator for survival analysis to handle censored data unbiasedly.

### 3. Dynamic Router Simulation (FR-004, FR-006)
- **Method**: Train a logistic regression model to predict optimal $k$ based on entropy and baseline difficulty.
- **Target**: "Optimal k" is the first $k$ where the code passes the test suite, derived from the **training set** convergence trajectory.
- **Evaluation**: The router is evaluated on a **held-out test set**. The FLOPs savings are calculated based on the **predicted k** (not the actual k) to avoid tautological validation. The router predicts k, and the cost is simulated based on that prediction.
- **Validation**: 5-fold cross-validation.
- **Baselines**: Random baseline ($k=1$), Optimal static baseline (Oracle).
- **Metric**: FLOPs savings vs. accuracy. Non-inferiority test ($\delta = 0.05$).

### 4. Robustness & Sensitivity (FR-005, FR-007)
- **Multiple Comparisons**: Holm-Bonferroni correction applied to all strata tests.
- **Sensitivity**: Sweep convergence threshold $k \in \{3, 4\}$.
- **Small Strata**: Use hierarchical mixed-effects models for strata with $< 50$ samples.

## Compute Feasibility & Escape Hatch

### CPU-First Strategy
- **Method**: Use a **sampled** subset (e.g., an initial set of problems) for initial validation and entropy clustering logic.
- **Inference**: Run `CodeLlama-7B` in 8-bit quantization on CPU (if feasible) or use a smaller distilled model for the CPU validation mode.
- **Limitation**: Full 7B inference on CPU for $N=164 \times 10$ samples is infeasible within 6h/7GB RAM.

### GPU Escape Hatch (Kaggle Auto-Offload)
- **Trigger**: If CPU run fails or exceeds time/memory, the execution stage auto-offloads to Kaggle GPU (~16 GB VRAM).
- **Plan**: Run full dataset (HumanEval + MBPP) with `device="cuda"`, `load_in_8bit`.
- **Scaling**: If VRAM > 16GB, reduce $N$ (samples) or use a smaller model (e.g., CodeLlama-7B is target, but fallback to 13B if needed? No, spec says 7B).
- **Justification**: 7B model inference is the only faithful method for the research question. Simulating it on CPU is fabrication. The plan explicitly targets the GPU escape hatch for the primary analysis.

## Statistical Rigor

- **Multiple Comparisons**: Holm-Bonferroni correction applied to all strata tests.
- **Power Analysis**: Conducted to ensure combined N (HumanEval + MBPP) is sufficient for MDES $\rho=0.2$ at $\alpha=0.05$, power $\ge 0.8$. If underpowered (due to stratification/censoring reduction), explicitly state limitation and report confidence intervals.
- **Causal Claims**: Observational study. Claims framed as associational.
- **Collinearity**: Entropy and convergence are treated as distinct; collinearity diagnostics reported if used in router.
- **Significance Threshold**: Statistical significance threshold is set at a conventional level (source: Statistical significance, https://en.wikipedia.org/wiki/Statistical_significance).

## Decision/Rationale

| Method | CPU Form? | GPU Form? | Rationale |
|:--- |:--- |:--- |:--- |
| **Entropy Extraction** | Sampled (N=50) | Full (N=164+500) | 7B inference is GPU-bound. CPU form is a validation subset. |
| **Convergence Tracking** | Sampled | Full | Requires 7B inference. |
| **Logistic Regression** | Yes | Yes | Trivial on CPU. |
| **Survival Analysis** | Yes | Yes | Trivial on CPU. |

**Conclusion**: The plan uses a CPU-sampled validation mode for logic verification and a GPU-offloaded full mode for the primary scientific results. No synthetic stand-ins are used.