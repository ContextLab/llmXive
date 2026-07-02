---
action_items:
- id: 7d848720f0f9
  severity: science
  text: The evaluation of the SGT-MCTS algorithm (Table 1) relies on Node Recall (84.8%)
    and Edge Recall (79.0%) against a benchmark of 30 survey papers. The sample size
    (133 chains) is small for a graph of this scale. Please report confidence intervals
    or perform a statistical significance test (e.g., bootstrap) to confirm the 39.9-point
    gain over Beam@10 is not due to variance in the specific survey selection.
- id: 030d7b818e71
  severity: science
  text: 'The ''Strata Dataset'' for idea evaluation (Sec 4.2) uses publication venue
    (Top-tier vs. Rejected) as a proxy for idea quality. This introduces a circularity
    risk: the graph is trained on these papers, and the evaluation assumes the venue
    label is the ground truth. The authors must address whether the graph is merely
    memorizing venue-specific citation patterns rather than learning true methodological
    evolution, and provide an ablation or control to rule out this confound.'
- id: 879c40d142eb
  severity: science
  text: The human evaluation for idea generation (Sec 4.3) reports an 88% win rate
    for Intern-Atlas. The methodology states experts were 'permitted to consult external
    academic search tools.' If experts could verify the novelty of the generated ideas
    using the same graph or external sources, the 'blind' nature of the evaluation
    is compromised. Clarify if the experts had access to the Intern-Atlas graph during
    the pairwise comparison, as this would invalidate the claim of independent validation.
artifact_hash: 8cf472ae2a887b5d12e0bb466a1ee80bacbf411e923611b73e3a5325c617cf94
artifact_path: projects/PROJ-569-intern-atlas-a-methodological-evolution/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:31:03.013108Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The scientific evidence supporting the core claims of Intern-Atlas is generally robust in terms of scale (1M+ papers) and the logical flow of the methodology, but the statistical rigor of the evaluation section requires strengthening to rule out alternative explanations for the reported gains.

First, the evaluation of the SGT-MCTS algorithm (Section 4.1, Table 1) presents a massive performance gap (e.g., 84.8% Node Recall vs. 44.9% for Beam@10) based on a benchmark derived from only 30 survey papers (133 evolution chains). While the absolute numbers are impressive, the small sample size of the ground truth makes the results susceptible to selection bias. The authors should provide confidence intervals (e.g., via bootstrapping over the 30 surveys) or a statistical significance test to demonstrate that the observed improvements are not artifacts of the specific survey selection. Without this, the claim of "strong alignment" remains descriptive rather than statistically proven.

Second, the evaluation of the idea evaluator (Section 4.2) relies on the "Strata Dataset," where the ground truth for idea quality is the publication venue (Top-tier vs. Rejected). This creates a potential circularity: the graph is constructed from the corpus of these papers, and the evaluation metric assumes that the venue label perfectly reflects the quality of the underlying method. If the graph simply learns the citation patterns that correlate with high-impact venues (a form of memorization), it will naturally score those papers higher. The authors need to address this confound, perhaps by showing that the graph can distinguish quality within a single venue or by using an external, non-venue-based metric for a subset of the data.

Finally, the human evaluation for idea generation (Section 4.3) notes that experts were "permitted to consult external academic search tools." If these tools included the Intern-Atlas graph itself or if the experts could easily verify the "novelty" claims using the same data source the system was trained on, the "blind" nature of the pairwise comparison is compromised. The review must clarify whether the experts had access to the Intern-Atlas infrastructure during the evaluation. If they did, the high win rate (88%) may reflect the experts' familiarity with the graph's output rather than the intrinsic quality of the generated ideas compared to baselines.

Overall, the infrastructure is impressive, but the validation metrics need to be decoupled from the training data's inherent biases to fully support the claim of "foundational data layer" utility.
