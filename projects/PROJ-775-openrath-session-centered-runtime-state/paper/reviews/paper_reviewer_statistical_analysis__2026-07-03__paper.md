---
action_items:
- id: 5f44e9d17754
  severity: writing
  text: 'Definition of "Deterministic" vs. Statistical Variance: The paper repeatedly
    claims "deterministic" behavior for lineage export and workflow composition (Section
    7, Table 4). If the system is truly deterministic, statistical variance is zero,
    and standard statistical tests are inapplicable. If there are stochastic elements
    (e.g., in tool selection or memory recall when not in "smoke test" mode), the
    paper must specify the number of trials ($n$) and the observed variance (e.g.,
    standard deviation'
- id: 4b5d8c1abd02
  severity: writing
  text: 'Evidence for "Memory Plane" Claims: The Memory component is listed as "evidence-gated"
    and "not yet substantiated" (Section 5, Table 2; Section 9, Table 5). While the
    authors correctly avoid making unsupported claims, the criteria for moving this
    from "gated" to "supported" should include a statistical power analysis or a defined
    sample size for future evaluation. Merely stating that "source anchors are absent"
    is a software engineering status; a statistical review requires knowing what data
    vol'
- id: ee5e7175af77
  severity: writing
  text: 'Scope of "Focused Tests": Section 7 mentions "focused tests" and a pytest_report
    as evidence. For a statistical review, it is crucial to know if these tests involve
    randomized inputs or edge-case sampling. If the evaluation is purely deterministic
    (fixed inputs, fixed outputs), the claim of "inspectability" is a software engineering
    property, not a statistical one. The text should explicitly state that no statistical
    generalization is claimed for these specific results to avoid misinterpretation'
artifact_hash: b43d862ac677a6650e267995c2525b6b2c2aa8062f07856fac7d91db4441a929
artifact_path: projects/PROJ-775-openrath-session-centered-runtime-state/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T04:43:35.290537Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The manuscript focuses on a system architecture (OpenRath) and a programming model centered on a `Session` object, rather than on empirical performance metrics or hypothesis testing. Consequently, traditional statistical analysis (e.g., t-tests, ANOVA, confidence intervals for benchmark scores) is absent, which is consistent with the authors' explicit scoping of the work to "deterministic runtime properties" and "audit-first" evidence (Abstract; Section 7).

However, from a statistical rigor perspective regarding reproducibility and claim substantiation, the following points require clarification:

1.  **Definition of "Deterministic" vs. Statistical Variance:** The paper repeatedly claims "deterministic" behavior for lineage export and workflow composition (Section 7, Table 4). If the system is truly deterministic, statistical variance is zero, and standard statistical tests are inapplicable. If there are stochastic elements (e.g., in tool selection or memory recall when not in "smoke test" mode), the paper must specify the number of trials ($n$) and the observed variance (e.g., standard deviation of execution time or token usage) to support the claim of "replayability." Currently, the text implies reproducibility without defining the experimental conditions (seeded vs. unseeded) under which this was measured.

2.  **Evidence for "Memory Plane" Claims:** The `Memory` component is listed as "evidence-gated" and "not yet substantiated" (Section 5, Table 2; Section 9, Table 5). While the authors correctly avoid making unsupported claims, the criteria for moving this from "gated" to "supported" should include a statistical power analysis or a defined sample size for future evaluation. Merely stating that "source anchors are absent" is a software engineering status; a statistical review requires knowing what data volume or trial count would be necessary to validate the "recall/commit quality" mentioned in Section 9.

3.  **Scope of "Focused Tests":** Section 7 mentions "focused tests" and a `pytest_report` as evidence. For a statistical review, it is crucial to know if these tests involve randomized inputs or edge-case sampling. If the evaluation is purely deterministic (fixed inputs, fixed outputs), the claim of "inspectability" is a software engineering property, not a statistical one. The text should explicitly state that no statistical generalization is claimed for these specific results to avoid misinterpretation by readers expecting performance benchmarks.

The paper is sound in its decision to avoid overclaiming on statistical performance where none was measured. The primary revision needed is to tighten the language around "determinism" and "reproducibility" to ensure it does not inadvertently imply statistical robustness where only software determinism exists.
