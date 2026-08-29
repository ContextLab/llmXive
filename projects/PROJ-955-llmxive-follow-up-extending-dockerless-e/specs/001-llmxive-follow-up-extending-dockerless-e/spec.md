# Feature Specification: llmXive follow-up: extending "Dockerless: Environment-Free Program Verifier for Coding Agents"

**Feature Branch**: `001-static-dynamic-gap-analysis`  
**Created**: 2026-08-04  
**Status**: Draft  
**Input**: User description: "To what extent can static structural features (control flow and call graphs) capture the semantic correctness of LLM-generated code patches, and what specific types of code behaviors (e.g., dynamic dispatch, external API calls) cause static approximations to diverge from dynamic execution ground truth?"

## User Scenarios & Testing

### User Story 1 - Static Feature Extraction Pipeline (Priority: P1)

The system must ingest LLM-generated code patches from the SWE-Gym and Multi-SWE-RL datasets and generate static structural representations (Control Flow Graphs and Call Graphs) for every patch, serializing them into a structured format for analysis.

**Why this priority**: This is the foundational data layer. Without successfully converting source code into static graphs for the entire dataset, no correlation analysis or error mining can occur. It is the prerequisite for all subsequent research steps.

**Independent Test**: The pipeline can be tested by running it on a small, known subset of patches (e.g., 50 patches) and verifying that valid JSON graph files are produced for [deferred] of the input, with no runtime errors on valid Python/C++ syntax.

**Acceptance Scenarios**:

1. **Given** a repository with 3.7k issues containing Python and C++ patches, **When** the extraction script is executed, **Then** a JSON file containing the CFG and CG is generated for every patch within the 6-hour CI limit.
2. **Given** a patch with complex recursion or external dependencies, **When** the graph generator runs, **Then** the system handles the node/edge creation without crashing and marks unresolvable external calls as "external" nodes rather than failing.
3. **Given** a patch that fails to compile or parse, **When** the extractor runs, **Then** the system logs the failure reason and skips the patch, ensuring the pipeline continues for the remaining [deferred] of the dataset.

---

### User Story 2 - Correlation & Classification Analysis (Priority: P2)

The system must train a lightweight machine learning classifier (e.g., Random Forest) using the extracted static features to predict the ground-truth dynamic execution result (pass/fail) and calculate performance metrics (AUC, Precision, Recall).

**Why this priority**: This directly addresses the primary research question: "To what extent can static features capture semantic correctness?" It provides the quantitative evidence needed to determine if static analysis is a viable proxy.

**Independent Test**: The analysis can be tested by running the classifier on a held-out test set (e.g., [deferred] of the data) and verifying that the model produces a confusion matrix and AUC score, even if the score is low (a low score is a valid result).

**Acceptance Scenarios**:

1. **Given** the feature vectors and ground-truth labels for [deferred] patches ([deferred] training), **When** the model is trained, **Then** the model achieves a convergence state and outputs a confusion matrix on the 740 patch test set.
2. **Given** the trained model, **When** it predicts on the test set, **Then** the system calculates and logs the AUC, Precision, and Recall metrics.
3. **Given** a dataset split, **When** the analysis runs, **Then** the system performs a chi-squared or Fisher's exact test to determine if the association between static features and dynamic correctness is statistically significant (p < 0.05).

---

### User Story 3 - Error Case Mining & Divergence Categorization (Priority: P3)

The system must isolate patches where the static model fails (False Positives and False Negatives) and automatically categorize these errors based on specific code patterns (e.g., "dynamic dispatch," "mocked API," "concurrency race").

**Why this priority**: This addresses the secondary research question: "what specific types of code behaviors... cause static approximations to diverge?" It transforms raw error rates into actionable qualitative insights about the "semantic gap."

**Independent Test**: The mining logic can be tested by feeding it a pre-labeled set of known failure modes (e.g., a patch known to fail due to dynamic dispatch) and verifying that the system correctly tags it as a "dynamic dispatch" error.

**Acceptance Scenarios**:

1. **Given** the model predictions and ground truth, **When** the error miner runs, **Then** it identifies all False Positives (static says pass, dynamic says fail) and False Negatives (static says fail, dynamic says pass).
2. **Given** a False Positive/Negative patch, **When** the pattern matcher runs, **Then** it assigns a label from the predefined taxonomy (e.g., "dynamic dispatch," "external I/O") based on the static graph structure.
3. **Given** the categorized errors, **When** the summary report is generated, **Then** it produces a frequency distribution showing which code behaviors account for the majority of the divergence.

---

### Edge Cases

- **What happens when a patch contains obfuscated or highly irregular code that `pycg` or `clang-query` cannot parse?** The system must skip the patch, log the specific error, and exclude it from the statistical analysis to prevent pipeline crashes.
- **How does the system handle patches where the ground-truth test execution result is missing or ambiguous (e.g., timeout vs. fail)?** The system must treat ambiguous results as missing data and exclude them from the training set to avoid label noise.
- **What if the dataset contains patches with no control flow (e.g., single-line variable assignments)?** The system must handle graphs with zero or minimal nodes gracefully, ensuring the feature vector is not empty or causing division-by-zero errors in metric calculation.

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest the SWE-Gym and Multi-SWE-RL datasets (3.7k issues) and extract source code and ground-truth test logs for every patch (See US-1).
- **FR-002**: System MUST generate Control Flow Graphs (CFG) and Call Graphs (CG) for all Python and C++ patches using `pycg` and `clang-query` respectively, serializing results as JSON (See US-1).
- **FR-003**: System MUST compute a feature vector for each patch including node degree, path length, recursion depth, and presence of external function calls (See US-2).
- **FR-004**: System MUST train a lightweight classifier (Random Forest or Logistic Regression) on the static features to predict the binary ground-truth label (pass/fail) (See US-2).
- **FR-005**: System MUST isolate and categorize False Positives and False Negatives into specific code behavior categories (e.g., dynamic dispatch, external I/O) (See US-3).
- **FR-006**: System MUST perform a statistical significance test (Chi-squared or Fisher's exact) to validate the association between static features and dynamic correctness (See US-2).
- **FR-007**: System MUST measure and report the total runtime and memory footprint of the pipeline to verify feasibility on a 2-core CPU runner (See US-1).

### Key Entities

- **Patch**: A unit of code change from the dataset, containing source code, language type, and ground-truth execution result.
- **StaticGraph**: A JSON representation of a patch's Control Flow Graph or Call Graph, containing nodes, edges, and metadata.
- **FeatureVector**: A numerical representation of a patch derived from its StaticGraph, used as input for the classifier.
- **ErrorCase**: A specific patch instance where the static prediction diverges from the dynamic ground truth, tagged with a divergence category.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The correlation between static features and dynamic correctness (AUC score) is measured against the baseline of random guessing (AUC=0.5) to determine predictive value (See US-2).
- **SC-002**: The rate of divergence (False Positive + False Negative rate) is measured against the total number of analyzed patches to quantify the "semantic gap" (See US-3).
- **SC-003**: The distribution of error categories (e.g., % of errors due to dynamic dispatch) is measured against the total error count to identify specific failure modes (See US-3).
- **SC-004**: The pipeline runtime is measured against the 6-hour GitHub Actions free-tier limit to confirm compute feasibility (See US-1).
- **SC-005**: The statistical significance (p-value) of the association between static features and correctness is measured against the alpha threshold of 0.05 (See US-2).

## Assumptions

- The SWE-Gym and Multi-SWE-RL datasets contain complete, parseable source code for the 3.7k issues and reliable ground-truth test execution logs (pass/fail) for the same issues.
- The `pycg` and `clang-query` tools can be installed and run on a standard GitHub Actions free-tier runner (Ubuntu, 2 CPU, ~7 GB RAM) without requiring GPU acceleration or specialized hardware.
- The dataset size (thousands of patches) and the resulting graph structures will fit within the ~7 GB RAM and ~14 GB disk constraints of the free-tier runner; if memory usage exceeds this, the analysis will proceed on a stratified random sample of the dataset.
- The ground-truth test execution results are independent of the static analysis features, ensuring no circularity in the validation (i.e., the static graphs are not derived from the test execution logs).
- The "dynamic dispatch" and "external API" categories can be reliably identified from the static Call Graph structure (e.g., by detecting calls to functions not defined in the local repository or specific dynamic resolution patterns).
- The dataset variables (predictors: static features; outcome: pass/fail) are sufficient for the analysis; if the dataset lacks specific metadata required to categorize certain error modes (e.g., explicit "mocked API" flags), the categorization will rely on heuristic pattern matching in the static graph.
