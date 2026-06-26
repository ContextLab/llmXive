---
action_items:
- id: 2d72f08eb9a3
  severity: science
  text: Clarify whether claims about model failures are theoretical or empirical.
    If empirical, provide statistical aggregation or cite specific quantitative studies
    more rigorously.
- id: 7fcc1599a80b
  severity: science
  text: Address the N=1 nature of the provided model traces (e.g., the '20 questions'
    example) and discuss alternative explanations like training data distribution.
artifact_hash: 924b893a4650c3044c8ebca795788f41846a7a72e06ec4cbf52905fb73429333
artifact_path: projects/PROJ-746-the-topological-trouble-with-transformer/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-26T10:28:34.830161Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The manuscript presents a compelling theoretical argument regarding the topological limitations of feedforward transformers in state tracking. However, from a scientific evidence perspective, the empirical claims regarding model failures lack quantitative rigor. Section 2 ("State tracking") relies heavily on anecdotal evidence, specifically single-trace examples from "Gemini 3 (Fast)" and "Gemini 2.5 Flash" (lines 130-160). While illustrative, N=1 traces do not constitute robust scientific evidence for general architectural limitations. The paper cites works like Lepori et al. (2025) to support claims about "delayed disambiguation" (lines 230-240), but does not summarize the statistical significance or effect sizes from those studies. To strengthen the central claim that "temporally extended cognition requires... recurrent architectures," the authors should either present systematic benchmark results quantifying failure rates across models or explicitly frame the empirical examples as illustrative case studies rather than evidence of a general phenomenon. Additionally, the taxonomy in Table 1 (lines 380-420) is theoretical; if any empirical performance data exists for the cited architectures, it should be summarized to support the "promising directions" section. Without quantitative backing, the argument remains a theoretical position rather than an evidence-based conclusion. Furthermore, alternative explanations for the observed failures (e.g., training data distribution rather than architectural topology) are not sufficiently ruled out. The authors should discuss how the cited empirical studies controlled for confounding variables like context window size or pretraining corpus. Strengthening the evidentiary basis for the transition from theoretical limitation to empirical necessity is crucial for the paper's impact.
