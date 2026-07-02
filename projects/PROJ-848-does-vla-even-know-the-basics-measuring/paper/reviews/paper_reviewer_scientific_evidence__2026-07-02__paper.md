---
action_items:
- id: e47ace799e79
  severity: science
  text: "The statistical interpretation of 'near-chance' performance requires explicit\
    \ reporting of the calculated Delta (\u0394) values for each category in the main\
    \ text or a summary table, rather than only in the appendix. Currently, readers\
    \ cannot verify if specific model scores (e.g., 52% on Symmetry) are statistically\
    \ distinguishable from 50% without manual calculation."
- id: 17eae4379429
  severity: science
  text: The claim that 'no evaluated VLA reaches above-random performance on Symmetry
    or Counting' relies on aggregated scores. The paper should explicitly report the
    standard error or confidence intervals for these specific category averages to
    confirm that the mean is not significantly different from 0.5, given the N=300
    sample size.
- id: de406bd34564
  severity: science
  text: The linear intent probing results (Figure 4, Table 3) show high retention
    in intermediate layers but low action success. The paper should clarify if the
    probe training set overlaps with the evaluation set. If the probe is trained on
    the same 1,720 items used for evaluation, the 'retention' metric may be overfitting
    to the specific dataset rather than measuring generalizable internal representations.
- id: 4736c7eae4ba
  severity: science
  text: "The mitigation experiments (Table 10) use a very small subset of categories\
    \ (Emotion, Attribute, Color, Shape) and a single model (\u03C00). The conclusion\
    \ that 'lightweight interventions are useful but limited' is based on insufficient\
    \ statistical power. The authors should either expand the ablation to more categories/models\
    \ or temper the claim to reflect the limited scope of the evidence."
artifact_hash: b7bf68dc7049e64af55a4f743a5addf0de48270ccdf470df63d9da46224951a5
artifact_path: projects/PROJ-848-does-vla-even-know-the-basics-measuring/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T20:33:15.346224Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a well-structured empirical study with a clear hypothesis: VLA fine-tuning degrades commonsense knowledge retention. The sample size is substantial (1,720 unique items, 3,440 episodes), and the use of left/right swapping to control for positional bias is a strong methodological choice that enhances the robustness of the success rate metric. The decomposition of task success into perception, knowledge, and control is conceptually sound and helps isolate the specific failure mode (knowledge loss vs. control failure).

However, the statistical evidence supporting the central claims requires tighter presentation. While Appendix A defines the chance margin $\Delta$ (approx. 5.7% for N=300), the main text frequently describes results as "near chance" or "at random threshold" without explicitly stating whether the observed means fall outside the $0.5 \pm \Delta$ interval. For instance, the claim that "no evaluated VLA reaches above-random performance on Symmetry" is critical; if the best score is 52%, it is within the noise margin of the 50% baseline. The authors should explicitly report the statistical significance (or lack thereof) for these borderline cases in the main results table or text to avoid over-interpreting noise as a trend.

Furthermore, the linear probing analysis (RQ4) is compelling but lacks a crucial detail regarding data leakage. The text states probes are trained on "hidden states from all tokens of every transformer layer" for "each episode." If the probe is trained and evaluated on the same 1,720 items used for the main benchmark, the high "Retention" scores (e.g., 75% for Magma) may reflect overfitting to the specific dataset rather than a generalizable internal representation of the knowledge. The authors must clarify if the probe training set is disjoint from the evaluation set or if cross-validation was used. Without this, the claim that "information remains internally represented" is weakened by the possibility of memorization.

Finally, the mitigation experiments (Discussion) are based on a very small subset of categories and a single model. While the direction of the results is interesting, the sample size is too small to support the broad conclusion that "lightweight interventions are useful but limited." The evidence here is suggestive but not yet robust enough to generalize to the entire Act2Answer suite.
