---
action_items:
- id: c65e5a510e16
  severity: science
  text: The skill transfer experiment (Section 5.3) relies on a single task subclass
    (frontend page generation) with only 10 in-domain and 5 held-out tasks. This sample
    size is insufficient to support the broad claim that 'skill injection is high
    variance' or to generalize findings about creator-consumer fit. The authors must
    either expand the skill evaluation to multiple task classes or explicitly frame
    these results as a preliminary case study rather than a generalizable finding.
- id: 834995eb2395
  severity: science
  text: The human judge calibration study (Table 4) uses a sample of n=48 (24 text,
    24 visual). While the text route shows reasonable correlation (Spearman 0.790),
    the visual route shows negative correlation. Given the paper's heavy reliance
    on visual artifact evaluation, this sample size is too small to robustly characterize
    the failure mode of visual judges. A larger human audit (e.g., n > 100) stratified
    by artifact type is required to validate the scoring protocol.
- id: d6d26972fb90
  severity: science
  text: The construction funnel (Figure 2) reports a reduction from 5,291 raw instances
    to 852 final tasks. The paper lacks a statistical breakdown of *why* instances
    were rejected at each gate (e.g., % rejected for missing fixtures vs. ambiguous
    prompts). Without this, it is impossible to assess if the final benchmark is biased
    toward 'easy' or 'self-contained' tasks, potentially inflating performance scores
    compared to the raw distribution of real workplace requests.
artifact_hash: 436f60fbb896e41d063ceb9811d2249a06e1b5eaa235430cfaccb20cf6596607
artifact_path: projects/PROJ-773-enterpriseclawbench-benchmarking-agents/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T13:14:48.235264Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a compelling benchmark derived from real enterprise sessions, but the scientific evidence supporting the robustness of the evaluation protocol and the generalizability of the skill-transfer claims requires strengthening.

First, the **skill evaluation** (Section 5.3) is the most significant statistical weakness. The authors claim that "skill injection is therefore high variance" and that outcomes depend on creator-consumer fit. However, this conclusion is drawn from a single task subclass (frontend page generation) with a total of only 15 tasks (10 in-domain, 5 held-out). With such a small sample size, the observed variance could easily be driven by idiosyncrasies of the specific HTML generation task rather than a general property of skill transfer. The current evidence does not support a general claim about skill evaluation; it only supports a case study on frontend generation. The authors should either expand this experiment to include 2-3 additional task classes (e.g., spreadsheet analysis, document drafting) to demonstrate consistency or significantly temper their conclusions to reflect the limited scope.

Second, the **human judge calibration** (Section 5.4, Table 4) relies on a sample of 48 packets. While the text route correlation (Spearman $\rho=0.790$) is encouraging, the visual route shows a negative rank correlation ($\rho=-0.259$). Given that the benchmark explicitly targets multimodal artifacts (spreadsheets, slides, HTML), the visual judge is a critical component of the evaluation. A sample of 24 visual artifacts is statistically underpowered to definitively characterize the failure mode of the visual judge or to claim that "evaluation on multimodal artifacts is not yet mature" as a general fact. A larger human audit, ideally stratified by artifact type (e.g., 50+ per category), is necessary to validate the scoring reliability.

Finally, the **construction funnel** (Figure 2) reports a massive attrition rate (5,291 $\to$ 852). The paper describes the gates (length, fixture, network, self-containment) but does not provide a quantitative breakdown of rejection rates per gate. This omission makes it difficult to assess potential selection bias. If the majority of rejections are due to "ambiguous tasks" or "missing fixtures," the resulting benchmark may systematically exclude the most complex, messy, or realistic enterprise scenarios, thereby inflating the reported performance of agents. A table detailing the number of instances rejected at each stage would significantly strengthen the evidence for the benchmark's representativeness.

The main leaderboard results (Section 5.2) appear robust given the 32 combinations tested, but the supporting analyses for skill transfer and judge reliability need larger sample sizes to support the paper's broader claims.
