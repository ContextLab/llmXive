---
action_items:
- id: 01f1fc192d2a
  severity: writing
  text: The claim 'no single model excels on all dimensions' (Abstract) is an over-generalization.
    Table 1 shows leaders vary, but the paper lacks statistical proof that no model
    is second-best in all others. Clarify if this is a qualitative summary or a robust
    statistical finding.
- id: a5709381cba5
  severity: science
  text: The assertion 'Physical scores correlate with video quality' (r=0.84) does
    not specify the model subset. If driven only by text-driven models, generalizing
    this to all world models is an overreach. Specify the exact subset used for this
    correlation.
- id: 8089565284c4
  severity: science
  text: The claim 'navigation is decoupled' relies on correlations from different
    evaluation subsets (158 vs 289 cases). Comparing across non-overlapping data risks
    over-interpreting independence. Clarify the data overlap used for the correlation
    analysis.
- id: 452650498d58
  severity: writing
  text: The statement 'Open-source models achieve competitive scores' is misleading
    as top performers (Wan 2.7, Kling 3.0) are API-only. Qualify this to 'some open-source
    models' to avoid implying general parity with closed models.
artifact_hash: 583182a56bc8cd93d801cd098b02d980b9a48cb375dac6cc8130da68f508615f
artifact_path: projects/PROJ-630-wbench-a-comprehensive-multi-turn-benchm/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T14:03:36.588567Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several strong claims regarding the state of interactive world models that slightly exceed the immediate evidence provided in the experimental results.

First, the central conclusion that "no single model excels on all dimensions" is a valid observation of the current landscape, but the phrasing suggests a definitive, universal law rather than a snapshot of the specific 20 models tested. While Table 1 (e002) supports the lack of a single "winner," the paper does not rigorously test the statistical significance of this "no dominance" claim across the entire space of possible models. It is a reasonable summary, but the language could be tempered to "no single model *among those evaluated* excels..." to avoid over-generalization.

Second, the claim that "Physical scores correlate with video quality" (Section 5.2, r=0.84) is presented as a general finding. However, the correlation analysis in Figure 5a is based on the navigation split (158 cases) and potentially a subset of models. The paper does not explicitly state whether this high correlation holds when comparing the full set of 289 cases or across all 20 models. If the correlation is driven primarily by the text-driven models (which tend to have high quality and high physics scores due to their generation nature) and not the action-conditioned models, then generalizing this as a fundamental property of world models is an overreach. The authors should clarify the exact subset of data and models used to derive this correlation coefficient.

Third, the assertion that "navigation is decoupled from other abilities" relies on a correlation of approximately zero. However, the evaluation protocol differs: navigation is evaluated on a specific subset (158 cases) for all models, while other metrics (like Setting Adherence) are evaluated on the full set (289 cases) for text-driven models. Comparing correlations across these different evaluation scopes without explicitly addressing the potential confounding factor of dataset size or composition could lead to an over-interpreted conclusion about the independence of these capabilities. The authors should clarify if the correlation analysis was performed on a strictly overlapping subset of data.

Finally, the statement that "Open-source models achieve competitive scores" (Conclusion) is slightly misleading given that the top performers in key categories (Wan 2.7, Kling 3.0) are API-only. While open models like LongCat and LingBot perform well, the phrasing implies a broader trend of open-source parity that the data does not fully support. Qualifying this to "some open-source models achieve competitive scores" would be more accurate.

These issues are primarily matters of precision in language and scope rather than fatal flaws, but addressing them will prevent the paper from over-claiming the universality of its findings.
