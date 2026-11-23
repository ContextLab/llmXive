# Research: The Influence of Network Topology on Neural Synchrony During Cognitive Tasks

## 1. Scientific Background

### 1.1 Research Question
How does the baseline topological organization of resting-state brain networks relate to the degree of neural synchrony exhibited during working memory task performance?

### 1.2 Theoretical Framework
- **Resting-State Networks (RSN)**: Intrinsic connectivity networks (e.g., Default Mode, Frontoparietal) exhibit stable topological properties (efficiency, modularity) that may constrain or facilitate task performance.
- **Neural Synchrony**: Task-induced increases in functional connectivity (synchrony) within specific networks (e.g., Frontoparietal) are associated with successful working memory performance.
- **Hypothesis**: Individuals with higher global efficiency in resting-state networks will exhibit greater task-evoked synchrony (Delta FC) in the frontoparietal network during working memory tasks.

### 1.3 Methodological Considerations
- **Associational Nature**: The study is observational (cross-sectional). No causal claims (e.g., "resting state *causes* task synchrony") will be made.
- **Multiple Comparisons**: Testing 4 metrics × 2 networks = 8 tests. FDR correction (Benjamini-Hochberg) is required.
- **Threshold Sensitivity**: Graph metrics depend on the proportional threshold. Sensitivity analysis across a range of thresholds is mandatory.
- **Circularity Avoidance**: The predictor (Rest Graph) and outcome (Task Evoked FC) are derived from distinct temporal windows (Rest vs. Task) to avoid tautology. The outcome is explicitly defined as **Task FC - Rest FC** to isolate the task effect.

## 2. Dataset Strategy

### 2.1 Primary Dataset Plan (Spec Requirement)
The spec requests **Human Connectome Project (HCP)** data.
- **Requirement**: Raw BOLD fMRI (Rest + Working Memory Task) for N=100 subjects.
- **Access Status**: **GATED**. HCP requires registration and a Data Use Agreement. It is **not** directly downloadable by a GitHub Actions free-tier runner.
- **Verified Sources**: The provided verified dataset block lists "HCP" URLs (e.g., `jonxuxu/HCP-flat`), but these are derived tables or unrelated data, **not** raw 4D NIfTI time-series required for graph analysis.

### 2.2 Feasible Alternative (Open Substitute)
To ensure the pipeline runs and produces reproducible results on CI, the plan uses a **verified open fMRI dataset** that contains both resting-state and task-based scans.
- **Selected Dataset**: **OpenNeuro ds000246** (n-back Working Memory Task + Resting State).
- **Justification**: 
  - Contains resting-state and **n-back Working Memory** task fMRI (verified).
  - Publicly available via `nilearn.datasets.fetch_openneuro` (no auth).
  - Fits within 7GB RAM/14GB disk if processed subject-by-subject (N=30).
- **Limitation**: The specific demographic and task parameters may differ from HCP. Results are **illustrative of the method**, not the specific HCP population.

### 2.3 Dataset Verification
- **Source**: OpenNeuro ds000246.
- **Task**: n-back (Working Memory).
- **Rest**: Yes.
- **Status**: **VERIFIED** (Primary source confirmed).
- **Fallback**: If ds000246 is unavailable, the pipeline halts with a "Dataset Unavailable" error. No other task is acceptable as it violates construct validity.

### 2.4 Dataset Strategy Table

| Dataset Name | Source Type | Access Method | Variables Available | Feasibility on CI |
|--------------|-------------|---------------|---------------------|-------------------|
| **HCP (Spec)** | Gated | API (Auth required) | Rest + WM Task, 200 regions | **FAIL** (Cannot download on CI) |
| **OpenNeuro ds000246** | Open | `nilearn.fetch_openneuro` | Rest + n-back Task, 200 regions | **PASS** (Verified open) |
| **Verified HCP Parquet** | Derived | HuggingFace | Metadata only (No BOLD) | **FAIL** (No time-series) |

**Decision**: The implementation will use **OpenNeuro ds000246** (n-back task) to validate the pipeline. The `research.md` will explicitly state: "Due to HCP access restrictions, the pipeline is validated on OpenNeuro ds000246. The scientific conclusions are limited to the methodological demonstration."

## 3. Methodological Rigor

### 3.1 Graph-Theoretical Metrics
- **Clustering Coefficient**: Measures local interconnectedness.
- **Characteristic Path Length**: Measures global integration.
- **Global Efficiency**: Inverse of path length; higher is better.
- **Modularity**: Degree of community structure.
- **Implementation**: `networkx` with proportional thresholding (default 20%).

### 3.2 Synchrony Calculation (Task-Evoked FC)
- **Primary Metric**: **Task-Evoked Functional Connectivity** (Delta FC = Task FC - Rest FC).
- **Secondary Metric**: Mean Functional Connectivity during task epochs (raw).
- **Networks**: Frontoparietal (FPN) and Default Mode (DMN).
- **Epochs**: Extracted from task event files (n-back blocks).
- **Avoiding Circularity**: The outcome is derived from the **Task** scan (minus Rest baseline), while the predictor is derived from the **Rest** scan. This ensures the "task" effect is isolated from baseline topology.

### 3.3 Statistical Analysis
- **Correlation**: Pearson `r` between graph metrics (Rest) and synchrony (Task Delta).
- **Correction**: FDR (Benjamini-Hochberg) for 8 tests.
- **Sensitivity**: Sweep thresholds {0.10, 0.20, 0.30}.

### 3.4 Power Analysis & Sample Size Contingency
- **N=30**: Expected N for OpenNeuro ds000246 after motion exclusion.
- **Power**: With N=30, can detect large correlations (r > 0.4) with [deferred] power. Moderate correlations (r=0.2) have low power ([deferred]).
- **Minimum N Threshold**: **N=25**. If the dataset yields fewer than 25 valid subjects, the pipeline halts and reports a "Power Insufficiency" error. This prevents a false negative conclusion.
- **Contingency**: If N < 25, the project will not proceed to statistical analysis.

### 3.5 Collinearity & Validity
- **Collinearity**: Graph metrics (e.g., efficiency vs. path length) are often inversely related. Results will be reported descriptively, acknowledging this.
- **Validity**: Metrics computed using standard `nilearn`/`networkx` implementations.

## 4. Compute Feasibility

- **CPU-First**: All operations (correlation, graph metrics) are vectorized NumPy/SciPy. No GPU needed.
- **Memory**: Process one subject at a time. Dataset size is ~GB.
- **Runtime**: 
  - Download/Preprocess: Approximately one to two hours (a representative cohort of subjects).
  - Metrics/Stats: Approximately one hour.
 - Total: [deferred] (within 6h limit).
- **GPU Escape Hatch**: Not required for this analysis (no deep learning).

## 5. Risk Mitigation

| Risk | Mitigation |
|------|------------|
| HCP API 429 Error | N/A (Using OpenNeuro). |
| Missing Task Scan | Exclude subject, log error, continue. |
| Disconnected Graph | If threshold 20% yields disconnected graph, try [deferred] (log warning). |
| Data Gating (HCP) | Switch to verified open OpenNeuro ds000246. |
| Power Insufficiency | Halt pipeline if N < 25. |
| Task Mismatch | If ds000246 unavailable, halt with "Dataset Unavailable" error. |

## 6. Construct Validity Mitigation

If the open dataset lacks the specific Working Memory task (e.g., fallback to Emotion task):
- **Action**: Re-label the outcome as "Task-Evoked Connectivity" (generic).
- **Caveat**: Explicitly state in the results that the cognitive domain (Emotion vs. WM) differs from the original hypothesis.
- **Fallback**: If no task data is available, the study will be limited to "Rest vs. Rest" correlation (circularity acknowledged) or halted.
- **Current Status**: ds000246 contains n-back (WM), so the specific hypothesis is testable.

## 7. Power & Sample Size Contingency

- **Target N**: 30 subjects.
- **Minimum N**: 25 subjects.
- **Power Limitation**: With N=30, the study is underpowered to detect small-to-moderate effects (r < 0.35). The analysis will be framed as a "methodological validation" of the pipeline and a "demonstration of large-effect detection" only.
- **Reporting**: If N < 25, the pipeline will output a "Power Insufficiency" report and terminate without generating correlation results.