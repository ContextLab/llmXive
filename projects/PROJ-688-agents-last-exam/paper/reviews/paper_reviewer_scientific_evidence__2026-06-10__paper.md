---
action_items:
- id: 840012d78111
  severity: science
  text: Add confidence intervals or standard errors to Table 1 (main results) to quantify
    uncertainty, as most configurations currently report single-run averages despite
    agent stochasticity.
- id: 9a053e6b5010
  severity: science
  text: Clarify whether the 'Last-Exam' tier stratification was defined a priori or
    derived from pilot results to avoid circularity in difficulty claims.
- id: e08a55cf6855
  severity: science
  text: Validate the public subset's representativeness across multiple model classes,
    not just Claude Code + Opus 4.7 (Fig. 7), to ensure generalizability.
artifact_hash: f7c4cdebe7449d4f51e2127cea7b868f7e8092d99e5958aa9629c6a9a2cf1332
artifact_path: projects/PROJ-688-agents-last-exam/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-10T19:27:21.108248Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The manuscript presents a substantial contribution with a large-scale benchmark (1.5K instances) and rigorous automated evaluation. However, the scientific evidence supporting the central performance claims requires strengthening in three areas.

First, statistical robustness is limited. Table 1 reports mean scores and pass rates for 14 configurations, but the caption notes that standard deviations are estimated from three runs for only a subset due to budget constraints. For the majority of entries, single-run averages are presented. Given the stochastic nature of LLM agents (e.g., tool selection, context management), single runs may not reflect true performance, and differences between configurations (e.g., 26.2% vs 24.2% overall pass rate) lack significance testing. I recommend adding confidence intervals or bootstrapped error bars to the main results table to allow readers to assess whether observed differences are meaningful.

Second, the definition of the "Last-Exam" tier warrants clarification. The text states this tier "comprises the hardest workflows, on which most agents achieve a 0% pass rate" (Section 4.1). If the task selection for this tier was informed by pilot runs of specific models, there is a risk of overfitting the benchmark difficulty to those architectures. Please explicitly state whether the three-tier stratification was defined a priori (e.g., based on expert complexity ratings) or post-hoc based on empirical pass rates. If the latter, acknowledge the potential bias in difficulty claims.

Third, the representativeness of the public subset (150 tasks) is validated only for one model/harness pair (Claude Code + Opus 4.7, Fig. 7, $r=0.89$). To support the claim that the public set is representative of the full pool across the field, this analysis should be extended to at least two other model classes (e.g., GPT-5.5 and a smaller open-weight model) to ensure the subset does not favor specific architectural strengths.

Finally, while the "gate-and-score" evaluation mode ensures verifiability, the 22% "Execution" failure rate (Fig. 5d) suggests that format errors contribute significantly to low pass rates. The abstract's claim of "2.6% average full pass rate" conflates reasoning failures with formatting failures. A sensitivity analysis showing pass rates if gates were relaxed slightly would help distinguish capability from compliance.
