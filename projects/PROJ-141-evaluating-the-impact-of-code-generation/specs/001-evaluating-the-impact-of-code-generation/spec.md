# Feature Specification: Evaluating the Impact of Code Generation Models on Developer Productivity

**Feature Branch**: `001-code-gen-productivity`  
**Created**: 2024-01-15  
**Status**: Draft  
**Input**: User description: "How does the use of large‑language‑model (LLM) code‑generation tools affect (i) developers' task‑completion time and (ii) the quality of the produced code compared with unaided coding?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Core Experiment Execution (Priority: P1)

A researcher can execute the controlled within-subject experiment where 30 participants complete coding tasks under two conditions: (a) LLM-assisted and (b) baseline (no assistance). The system presents problems, records timestamps, and streams code submissions to the server.

**Why this priority**: This is the foundational functionality—without the experiment running, no data can be collected, and no research question can be answered. All downstream analysis depends on this.

**Independent Test**: Can be fully tested by running the experiment interface with a single participant through both conditions and verifying that timestamps and code are logged correctly.

**Acceptance Scenarios**:

1. **Given** a participant with ≥1 year programming experience has been recruited and assigned to the study, **When** they complete the first coding problem in the LLM-assisted condition, **Then** the system records start_time and end_time in seconds with ≥1 second precision
2. **Given** a participant has submitted source code for a problem, **When** the submission is received, **Then** the system stores the UTF‑8 source file and logs it with a unique submission ID
3. **Given** a participant has completed all problems in the LLM-assisted condition, **When** they begin the baseline condition, **Then** the LLM assistant is disabled and the system logs the condition switch

---

### User Story 2 - Code Quality Assessment Pipeline (Priority: P2)

A researcher can run automated quality assessment on each submitted code sample, computing pass rate (test execution), cyclomatic complexity, test coverage, and static-analysis warnings.

**Why this priority**: Quality metrics are essential to answer the second part of the research question (code quality trade-offs). Without this, the study only measures speed, not the full productivity impact.

**Independent Test**: Can be fully tested by submitting known code samples and verifying that all four quality metrics are computed and stored correctly.

**Acceptance Scenarios**:

1. **Given** a submitted code file for a HumanEval problem, **When** the test suite is executed, **Then** the pass rate is computed as (number of passing tests / total tests) with ≥0.01 precision
2. **Given** a submitted code file, **When** cyclomatic complexity is computed using `radon cc`, **Then** the complexity score is recorded as an integer ≥1
3. **Given** a submitted code file, **When** test coverage is measured via `coverage.py`, **Then** coverage is recorded as a percentage ≥0% and ≤100%
4. **Given** a submitted code file, **When** static analysis is run using `pylint` (Python) or `checkstyle` (Java), **Then** the warning count is recorded as an integer ≥0

---

### User Story 3 - Statistical Analysis and Reporting (Priority: P3)

A researcher can run statistical analysis comparing LLM-assisted vs baseline conditions, computing paired t-tests (or Wilcoxon signed-rank if non-normal), effect sizes (Cohen's d), and 95% confidence intervals for all metrics.

**Why this priority**: This enables answering the research question with statistical rigor. It is the final analytical step that transforms raw data into research findings.

**Independent Test**: Can be fully tested by running the analysis script on a CSV dataset with known values and verifying that p-values, effect sizes, and confidence intervals are computed correctly.

**Acceptance Scenarios**:

1. **Given** a CSV dataset with paired completion times from both conditions for all 30 participants, **When** the statistical analysis is executed, **Then** a paired t-test (or Wilcoxon if non-normal) produces a p-value and Cohen's d effect size
2. **Given** multiple quality metrics are tested (pass rate, complexity, coverage, warnings), **When** the analysis is executed, **Then** multiple-comparison correction (e.g., Bonferroni or Holm) is applied to control family-wise error rate at α ≤ 0.05
3. **Given** the analysis is complete, **When** results are exported, **Then** all statistics include 95% confidence intervals with ±0.01 precision

---

### Edge Cases

- What happens when a participant's code causes a test suite to timeout or crash the execution environment?
- How does the system handle participants who drop out mid-experiment (incomplete within-subject data)?
- What happens when the LLM model exceeds the 6-hour GitHub Actions job time limit during participant sessions?
- How does the system handle code submissions that fail to compile or contain syntax errors?
- What happens when participants complete tasks significantly faster than expected (<30 seconds per problem)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST present problem statements from HumanEval or Codeforces datasets to participants with ≥95% successful problem loading rate (See US-1)
- **FR-002**: System MUST record start_time and end_time for each task with ≥1 second precision and store in UTC format (See US-1)
- **FR-003**: System MUST stream submitted source code to the server as UTF‑8 and assign a unique submission ID per problem (See US-1)
- **FR-004**: System MUST execute test suites on submitted code and compute pass rate as (passing tests / total tests) with ≥0.01 precision (See US-2)
- **FR-005**: System MUST compute cyclomatic complexity using `radon cc` and record as integer ≥1 (See US-2)
- **FR-006**: System MUST measure test coverage via `coverage.py` and record as percentage ≥0% and ≤100% (See US-2)
- **FR-007**: System MUST count static-analysis warnings using `pylint` (Python) or `checkstyle` (Java) and record as integer ≥0 (See US-2)
- **FR-008**: System MUST perform paired t-tests (or Wilcoxon signed-rank if non-normal) comparing LLM-assisted vs baseline conditions for all metrics (See US-3)
- **FR-009**: System MUST apply multiple-comparison correction (Bonferroni or Holm) to control family-wise error rate at α ≤ 0.05 when testing >1 hypothesis (See US-3)
- **FR-010**: System MUST compute effect sizes (Cohen's d) with 95% confidence intervals (±0.01 precision) for all comparisons (See US-3)
- **FR-011**: System MUST support sensitivity analysis for the 15-30% time reduction threshold by sweeping absolute diff ∈ {0.01, 0.05, 0.1} and reporting how false-positive/false-negative rates vary (See US-3)
- **FR-012**: System MUST log all participant IDs, condition assignments, and randomization seeds for reproducibility (See US-1)

### Key Entities

- **Participant**: Represents a recruited volunteer with ≥1 year programming experience; key attributes: ID, condition assignment, completion status
- **Problem**: Represents a coding task from HumanEval or Codeforces; key attributes: ID, difficulty level, problem statement, test suite
- **Submission**: Represents a participant's code submission for a problem; key attributes: ID, participant ID, problem ID, condition, source code, timestamp
- **Metric**: Represents a quality or time measurement; key attributes: submission ID, metric type (time, pass rate, complexity, coverage, warnings), value

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Task-completion time is measured against the baseline (unaided) condition mean, with effect size (Cohen's d) and 95% CI (See US-3)
- **SC-002**: Code quality (pass rate, cyclomatic complexity, coverage, warnings) is measured against the baseline condition mean for each metric (See US-3)
- **SC-003**: Statistical significance is measured against α ≤ 0.05 with multiple-comparison correction applied (See US-3)
- **SC-004**: Multiple-comparison correction is measured against family-wise error rate ≤ 0.05 using Bonferroni or Holm method (See US-3)
- **SC-005**: Sensitivity analysis is measured against absolute diff ∈ {0.01, 0.05, 0.1} for the time reduction threshold, reporting variation in false-positive/false-negative rates (See US-3)

## Assumptions

- Participants have stable internet connectivity and a modern web browser (Chrome/Firefox/Edge) to access the Flask web app
- GitHub Actions free-tier runner (2 CPU, ~7 GB RAM, ~14 GB disk, NO GPU, ≤6 h) can execute the full analysis pipeline end-to-end
- HumanEval benchmark and Codeforces problems are publicly accessible and can be downloaded without authentication
- JaCoText (Java) and StarCoder (Python) models are ≤1 GB and can run on CPU without CUDA or GPU acceleration
- 30 participants with ≥1 year programming experience can be recruited via Prolific or similar crowdsourcing platform
- Within-subject design (each participant completes both LLM-assisted and baseline conditions) is feasible without carryover effects
- Test suites from HumanEval and Codeforces are compatible with the execution environment on the GitHub Actions runner
- No participant dropout rate >20% (incomplete within-subject data will be excluded from paired analysis)
- The 15-30% time reduction target is based on industry expectations for LLM code-generation tools as stated in the idea
- All quality assessment tools (`radon`, `coverage.py`, `pylint`, `checkstyle`) are available and compatible with Python 3.9+
- Randomization is performed using Python's `random` module with fixed seed for reproducibility
- All code submissions are syntactically valid and can be parsed by the quality assessment tools
