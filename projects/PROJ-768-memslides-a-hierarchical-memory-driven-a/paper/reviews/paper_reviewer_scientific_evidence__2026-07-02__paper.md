---
action_items:
- id: 76d7e019e7c9
  severity: science
  text: The tool-memory evaluation relies on only nine matched pairs (Appendix Table
    2). While the sign test shows significance for Strict Verify and Core Tool Time
    Ratio, the sample size is too small to rule out random variance or specific prompt
    sensitivity. The authors should explicitly frame these as 'diagnostic' findings
    and avoid generalizing to 'reliable localized editing' without a larger, randomized
    test set.
- id: 001619205666
  severity: science
  text: The persona-alignment results (Table 1) show large effect sizes (e.g., +3.30
    on Content for GPT-5), but the evaluation relies on LLM-as-a-judge without reporting
    inter-rater reliability (e.g., Cohen's kappa) or variance across the three blind
    votes per dimension. Without this, the robustness of the 0-10 scale scores against
    judge bias is unclear.
- id: aa03762dac5e
  severity: science
  text: The profile bank construction involves a 'seeded completion' step using a
    registry to fill missing fields (Appendix A.4). This introduces a potential confound
    where the 'memory' effect might partly reflect the quality of the seed registry
    rather than the agent's ability to learn from history. The analysis should control
    for or discuss the impact of this synthetic data generation on the persona-alignment
    scores.
artifact_hash: d44b33b66588093736bc35436b4297f50da94321f7a3c7c12e6ba0ea57e820cd
artifact_path: projects/PROJ-768-memslides-a-hierarchical-memory-driven-a/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T09:26:35.434330Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The scientific evidence presented for the MemSlides framework is generally sound in its experimental design but relies on small sample sizes and LLM-based evaluation metrics that require stronger robustness checks.

The primary quantitative evidence for the **tool-memory** component comes from a diagnostic matched-pair setting involving only nine pairs (Appendix Table 2). While the authors correctly apply a sign test and report p-values (e.g., p=0.0195 for Strict Verify), the absolute sample size (N=9) is extremely low for drawing broad conclusions about "reliable localized editing." The results are highly sensitive to the specific prompts chosen; for instance, one pair (P7) shows a loss in Closed-Loop Completion. The authors appropriately label this as "diagnostic," but the central claim that tool memory enhances reliability should be tempered to reflect that this evidence is limited to a narrow, controlled subset of tasks. A larger, randomized set of modification requests would be necessary to support a stronger claim of general reliability.

For the **user profile memory** component, the evidence rests on persona-alignment judgments (Table 1) with large reported effect sizes (e.g., +3.30 points on Content for GPT-5). However, the evaluation protocol relies on LLM-as-a-judge without reporting inter-rater reliability metrics (e.g., Cohen's kappa or Krippendorff's alpha) across the three blind votes mentioned in the appendix. Without these statistics, it is difficult to assess the stability of the scores against potential judge bias or variance. Additionally, the "Specificity" metric uses distractor personas, but the analysis does not explicitly rule out the possibility that the model is simply overfitting to the specific distractor set rather than learning a generalizable persona.

A significant methodological concern lies in the **profile bank construction** (Appendix A.4). The authors describe a "seeded completion" step where missing profile fields are filled using a "role-preference registry." This means the "long-term memory" being tested is partially synthetic and derived from a static registry rather than purely from accumulated user interaction history. This introduces a confound: the performance gains might reflect the quality of the seed registry or the prompt engineering used to fill it, rather than the agent's ability to learn and retrieve preferences from a dynamic history. The paper should clarify the extent to which the results depend on this synthetic completion versus genuine learning from interaction traces.

Finally, while the **general-quality metrics** (Table 2) show that MemSlides remains competitive, the diversity metric (Vendi score) is computed on a suite level rather than per-deck, which limits the granularity of the analysis regarding visual variety. The evidence supports the hypothesis that memory separation improves specific, targeted behaviors, but the sample sizes and reliance on synthetic profile data prevent a definitive conclusion about broad, real-world efficacy.
