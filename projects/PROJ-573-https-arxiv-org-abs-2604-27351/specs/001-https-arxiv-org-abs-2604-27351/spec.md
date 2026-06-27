# Feature Specification: Heterogeneous Scientific Foundation Model Collaboration Benchmark

**Feature Branch**: `[001-heterogeneous-collaboration]`  
**Created**: 2026-06-23  
**Status**: Draft  
**Input**: User description: "Do heterogeneous scientific foundation models (time‑series, tabular, text) achieve better collaborative task performance when they maintain modality‑specific expertise through specialized interfaces, compared to when they are forced into unified language‑only architectures?"  

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Run Full Benchmark (Priority: P1)

A scientific researcher wants to evaluate whether a heterogeneous collaboration pipeline outperforms a unified language‑only pipeline on a suite of multi‑modal scientific tasks.

**Why this priority**: This is the core value‑proposition of the project; without a runnable benchmark the research question cannot be answered.

**Independent Test**: Execute the benchmark script on a fresh environment with default parameters and verify that a results report (CSV + summary PDF) is produced within the allotted compute budget.

**Acceptance Scenarios**:

1. **Given** the benchmark repository is cloned and dependencies installed, **When** the researcher runs `python run_benchmark.py --config default.yaml`, **Then** the system downloads the required datasets (< 5 GB total), runs inference for all tasks, and outputs a `results.csv` file and `summary.pdf` within 4 hours of wall‑clock time.  
2. **Given** the benchmark finishes, **When** the researcher opens `summary.pdf`, **Then** the report contains (a) mean accuracy for Condition A (heterogeneous condition) and Condition B (unified condition), (b) the absolute difference expressed as a percentage, and (c) a paired‑t test p‑value.
3. **Given** a task input lacks one of the expected modalities (e.g., no clinical notes), **When** the benchmark processes that task, **Then** the system logs a warning and proceeds with available modalities, marking the missing modality contribution as zero in the aggregated results.
4. **Given** a modality‑specific model exceeds the predefined per‑task inference limit, **When** the timeout threshold is reached, **Then** the system aborts that task, records it as a failure in `results.csv`, and continues processing remaining tasks.

---

### User Story 2 – Heterogeneous Modality‑Specific Orchestration (Priority: P2)

A data engineer wants to add a new modality (e.g., imaging) to the heterogeneous pipeline without breaking existing tasks.

**Why this priority**: Extensibility is essential for future scientific workflows; the system must support plug‑and‑play modality models.

**Independent Test**: Add a dummy "image" modality configuration file and run a single task that includes the new modality; verify that the pipeline processes it using the specified model and includes its output in the final prediction.

**Acceptance Scenarios**:

1. **Given** a new modality configuration `image.yaml` pointing to a lightweight image‑transformer (< 1 GB), **When** the engineer runs `python run_task.py --task-id 3 --add-modality image`, **Then** the system loads the image model, processes the image data, and combines its embedding with the other modality embeddings to produce a final prediction without error.

---

### User Story 3 – Unified Text‑Only Translation (Priority: P3)

A researcher prefers a language‑only workflow and wants the system to automatically translate all inputs to text before feeding them to a single LLM.

**Why this priority**: Some teams may lack resources for multiple models; supporting a unified path ensures broader adoption.

**Independent Test**: Run the benchmark with the `--mode unified` flag and confirm that (a) time‑series data are summarised into statistical sentences, (b) tabular rows are rendered as CSV‑style text, and (c) the LLM processes the concatenated text to produce predictions.

**Acceptance Scenarios**:

1. **Given** the benchmark is invoked with `--mode unified`, **When** a task includes a time‑series file, **Then** the system outputs a textual summary (e.g., "Mean heart rate = 78 bpm, max = 120 bpm …") that is passed to the LLM.  

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST ingest public datasets (PhysioNet, selected UCI tabular sets, PubMed abstracts) and verify that total downloaded size ≤ 5 GB. (See US-1)
- **FR-002**: System MUST orchestrate modality‑specific models (TimeSeries‑Transformer, TabPFN, distilled LLM) via a routing layer that forwards each modality's raw input to its native model. (See US-1)
- **FR-003**: System MUST provide a unified translation layer that converts time‑series and tabular inputs into plain‑text representations according to a deterministic schema. (See US-3)
- **FR-004**: System MUST compute task‑specific evaluation metrics (classification F1, regression MAPE) and aggregate them into a mean accuracy score for each collaboration condition. (See US-1)
- **FR-005**: System MUST log all random seeds, model versions, and environment details to enable exact reproducibility of results. (See US-1)
- **FR-006**: System MUST enforce a per‑task inference wall‑time ≤ 5 minutes on 2 CPU cores; tasks exceeding this limit are aborted and recorded as failures. (See US-1)
- **FR-007**: System MUST generate a final results report (CSV + PDF) that includes (a) mean accuracy per condition, (b) percentage difference, (c) paired‑t test statistic and p‑value, and (d) bootstrap confidence interval computed with a sufficient number of bootstrap resamples. (See US-1)
- **FR-008**: System MUST support addition of new modality configurations via a YAML file without code changes. (See US-2)
- **FR-009**: System MUST handle missing modality inputs by either (i) skipping that modality in the heterogeneous condition or (ii) inserting a placeholder text in the unified condition. (See US-2)
- **FR-010**: System MUST retry failed dataset downloads up to **3** times before aborting. (See US-1)
- **FR-011**: System MUST use a statistical significance threshold of α ≤ 0.05 for the paired‑t test, consistent with convention in the scientific field (see Assumptions section). (See US-1)
- **FR-012**: System MUST log a warning and record missing modality contribution as zero when a task's input lacks an expected modality. (See US-1)
- **FR-013**: System MUST abort and record as failure any task where modality‑specific model inference exceeds 5 minutes. (See US-1)
- **FR-014**: System MUST support non‑parametric alternatives (Wilcoxon signed‑rank test) and report effect sizes with 95% confidence intervals as primary outcome alongside paired t‑test, to account for task‑level dependency and normality violations. (See US-1)

### Key Entities

- **Dataset**: Represents a public scientific dataset (time‑series, tabular, or text) with associated ground‑truth labels.
- **ModalityModel**: Encapsulates a pre‑trained model specialized for a single data modality, including its HF identifier and inference script.
- **Task**: A composite multi‑modal prediction problem linking 2–3 datasets and a target label.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The heterogeneous condition (A) achieves a mean accuracy that is **≥ [deferred] %** higher than the unified condition (B) on the task suite, measured against the independent ground‑truth labels. (Rationale: threshold determined empirically from pilot data; See US-1)
- **SC-002**: Inference MUST complete within the 5‑minute per‑task wall‑time limit on the prescribed hardware (2 CPU cores). (See US-1)
- **SC-003**: The entire benchmark (data download, inference for all tasks, reporting) consumes ≤ 4 hours of wall‑clock compute time on the reference environment (2 CPU, 8 GB RAM). (See US-1)
- **SC-004**: Reproducibility logs enable recreation of the primary results across **5 seeds** with different random seeds, where mean accuracy differences fall within a 95% CI (statistical equivalence). (See US-1)
- **SC-005**: The paired‑t test reports a p‑value **≤ 0.05** (or the clarified α‑level) when the observed accuracy gap meets the SC‑001 threshold. (See US-1)

## Assumptions

- Pre‑trained models are publicly available on HuggingFace and each weighs < 1 GB.
- No fine‑tuning is performed; all models operate in zero‑shot or few‑shot mode.
- Ground‑truth labels supplied by the original dataset creators are accurate and can be used as an independent validation source.
- The statistical analysis will use a paired‑t test with a default α‑level of **0.05** unless clarified (see FR‑011).
- The compute environment provides at least 2 CPU cores and 8 GB RAM; GPU acceleration is **out of scope** for the baseline benchmark.
- All external URLs (PhysioNet, UCI Repository, PubMed, RouteMark paper) remain reachable for the duration of the project.

---