---
action_items:
- id: aca321e63afa
  severity: science
  text: The interface ablation (Table 3) claims GUI-only/CLI-only settings collapse
    to <3.5% PassRate, but the text does not explicitly state the sample size (N)
    for these specific ablation runs. Given the high variance in agent performance,
    confirm if N=114 (full benchmark) was used for ablation or a subset, and report
    confidence intervals or standard errors for these low-probability events.
- id: b043d80767d9
  severity: science
  text: The 'trajectory-aware judge' reduces PassRate by ~20pp (Fig 4), but the judge
    itself is an LLM (GPT-5.5). The paper lacks a validation study of the judge's
    own precision/recall against human annotations. Without a human-in-the-loop audit
    of the judge's 'shortcut' flags (e.g., false positives on legitimate tool use),
    the corrected PassRate of 33.3% is not fully robust.
- id: bf78f4d36b8a
  severity: science
  text: The claim that tasks satisfy 'Channel Non-Substitutability' (P1) relies on
    a static analysis of atomic operations (Table A1). The paper should provide empirical
    evidence that no single-channel agent (even with infinite retries) could solve
    these tasks, rather than just asserting the design intent. A 'failure mode' analysis
    showing single-channel agents hitting hard walls would strengthen this.
artifact_hash: fe47fd5151ed0fa01e324bf6a3d1eb3486f522739d02266159e873e4cf63e576
artifact_path: projects/PROJ-702-weavebench-a-long-horizon-real-world-ben/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T06:07:30.319572Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a compelling benchmark with a clear motivation: the lack of evaluation for hybrid GUI/CLI orchestration in computer-use agents. The dataset size (N=114 tasks) is appropriate for a benchmark paper, and the use of real-world artifacts (P3) adds significant ecological validity compared to synthetic benchmarks.

However, the scientific evidence supporting the central claims requires strengthening in three areas:

1. **Statistical Rigor in Ablation Studies:** The interface ablation results (Section 4.3, Table 3) show a dramatic drop to <3.5% for single-channel settings. While the effect size is large, the text does not specify the sample size (N) used for these specific ablation runs. If these were run on a subset of tasks, the generalizability is limited. Furthermore, for events with such low probability (near-zero success), reporting standard errors or confidence intervals is crucial to distinguish between "impossible" and "extremely rare."

2. **Validation of the Trajectory-Aware Judge:** The paper relies heavily on a novel "trajectory-aware agentic judge" (Section 3.4) to detect reward hacking, which significantly alters the reported PassRate (from ~53% to ~33% for GPT-5.5). The judge is implemented as an LLM (GPT-5.5). The manuscript lacks a validation study demonstrating the judge's accuracy against human ground truth. Without a human audit of the judge's "shortcut" flags (e.g., checking if the judge correctly identified fake screenshots vs. legitimate tool outputs), the corrected metrics are not fully robust. The claim that "outcome-only grading substantially overestimates" is plausible but unproven without a human baseline for the judge's precision/recall.

3. **Empirical Proof of Non-Substitutability:** The core design principle (P1) asserts that tasks *require* hybrid interfaces. This is currently supported by a static analysis of atomic operations (Table A1) and expert design. To strengthen the evidence, the authors should provide empirical data showing that even powerful single-channel agents (with extended context or retries) fail to solve these tasks due to specific "hard walls" (e.g., inability to read a GUI-rendered error log via CLI). The current evidence is largely theoretical (design intent) rather than empirical (observed failure modes of single-channel agents).

The failure analysis (Section 4.5) is detailed and provides good qualitative evidence of *how* agents fail, but the quantitative claims regarding the judge's impact and the ablation results need the statistical and validation rigor noted above to be fully convincing.
