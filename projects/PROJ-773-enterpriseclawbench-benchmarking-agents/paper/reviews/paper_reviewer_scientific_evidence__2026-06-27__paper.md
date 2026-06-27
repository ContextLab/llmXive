---
action_items:
- id: 81954bfde5b3
  severity: science
  text: The visual judge shows negative human correlation (Spearman -0.259, Table
    2). Main leaderboard scores relying on visual artifacts are scientifically invalid
    until this is resolved or excluded.
- id: ba28efeb0671
  severity: science
  text: Skill transfer experiment uses only 15 tasks (10 in-domain, 5 held-out). Report
    confidence intervals or p-values for the reported deltas (e.g., +0.0681) to establish
    statistical significance.
- id: f217d0909a79
  severity: science
  text: The Lite set (120 tasks) selection process is not detailed. Provide stratification
    details to rule out selection bias in the main leaderboard results.
artifact_hash: 436f60fbb896e41d063ceb9811d2249a06e1b5eaa235430cfaccb20cf6596607
artifact_path: projects/PROJ-773-enterpriseclawbench-benchmarking-agents/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-27T00:54:30.535859Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: full_revision
---

The scientific evidence supporting the central claims of EnterpriseClawBench is currently insufficient due to validity and reproducibility concerns.

First, the **judge reliability** evidence undermines the main leaderboard. In Section "Judge Reliability" (Table 2), the visual judge shows a negative Spearman correlation with human raters (-0.259) and a high MAE (0.303). Since Figure 1 (Leaderboard) and Figure 3 (Statistics) indicate that visual artifacts (spreadsheets, slides, images) constitute a significant portion of the benchmark, the primary performance scores are not empirically valid. The claim that the benchmark evaluates "multimodal judging" is contradicted by the evidence that the visual judge is uncalibrated.

Second, the **skill evaluation** lacks statistical power. In Section "Skill Evaluation", the experiment relies on a single task subclass (frontend page generation) with only 10 in-domain and 5 held-out tasks. The reported deltas (e.g., +0.0681 for GPT-5.5) are presented without confidence intervals or significance testing. Given the stated "high variance" in skill injection, these effect sizes may be noise. A sample size of 15 is inadequate to support the claim of "native support for evaluating skill generalization."

Third, **reproducibility** is compromised. The benchmark data (852 tasks) is not released due to proprietary content. While the construction protocol is described, independent verification of the task difficulty distribution and the filtering funnel (Figure 2) is impossible. The selection of the 120-task Lite set is described as "manually audited" but lacks stratification details, raising risks of selection bias in the main results.

To proceed, the authors must either exclude visual scores from the main leaderboard or demonstrate a corrected visual evaluation metric. Statistical rigor must be added to the skill transfer analysis, and the Lite set sampling strategy must be fully disclosed to ensure the results are not artifacts of cherry-picking.
