---
action_items:
- id: 539be4588aa2
  severity: science
  text: "Revise the statement that d-OPSD \u201Cconsistently outperforms\u201D RLVR\
    \ and SFT baselines to accurately reflect the results (e.g., d-OPSD underperforms\
    \ RLVR on Math500 at sequence length 512)."
- id: e50807e722d7
  severity: science
  text: "Include statistical significance testing (e.g., confidence intervals or p\u2011\
    values) for the reported performance gains to substantiate claims of superiority."
- id: 2c726d7012e4
  severity: writing
  text: "Clarify the sample\u2011efficiency comparison methodology, ensuring that\
    \ the reported 10\u202F% step reduction accounts for identical compute budgets\
    \ and rollout strategies across methods."
artifact_hash: 5c8da21032033f700374cf269bb9ef61b58d8799f1e6049fc84e38c052b8b257
artifact_path: projects/PROJ-732-learning-from-the-self-future-on-policy/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-21T12:42:03.024789Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The manuscript introduces d‑OPSD, an on‑policy self‑distillation framework for diffusion LLMs (dLLMs). While the core idea—using self‑generated answers as suffix‑conditioned privileged information and applying step‑level KL divergence—is well motivated, several claims extend beyond what the presented evidence supports.

1. **Overstated Consistency of Superiority**  
   The abstract and conclusion assert that d‑OPSD “consistently outperforms” RLVR and SFT baselines across all four reasoning benchmarks. Table 2, however, shows a counter‑example: on the Math500 dataset with a generation length of 512 tokens, the RLVR baseline (diffu‑GRPO) achieves 39.2 % accuracy (highlighted in light blue) whereas d‑OPSD attains 37.8 %, a modest decline. The claim of consistent superiority therefore overreaches the empirical results. The authors should temper this language to reflect the nuanced performance landscape.

2. **Lack of Statistical Validation**  
   All performance numbers are presented as point estimates without any indication of variance or statistical significance. Given the modest absolute differences (often 1–2 % points), it is unclear whether the observed gains are robust or could be attributed to random seed effects. Including confidence intervals, standard deviations across multiple runs, or hypothesis‑testing results would substantiate the superiority claims and prevent inadvertent over‑interpretation.

3. **Sample‑Efficiency Comparison Ambiguities**  
   The paper claims that d‑OPSD requires “only around 10 % of the optimization steps by RLVR.” Table 3 lists the number of optimization steps for each method, but it does not clarify whether the two methods used identical batch sizes, learning‑rate schedules, or rollout counts per update. Since the authors’ pass@k sampling strategy (k = 8) incurs the same per‑step compute as the RLVR baseline, a more detailed accounting of total FLOPs or wall‑clock time would be needed to validate the sample‑efficiency claim.

4. **First‑of‑Its‑Kind Assertion**  
   The statement that d‑OPSD is “the first OPSD framework tailored for dLLMs” appears plausible given the cited literature, but the authors should explicitly discuss why prior works (e.g., d3LLM, CD4LM) do not qualify as OPSD, perhaps by contrasting on‑policy versus off‑policy training regimes. A brief justification would preempt potential disputes over novelty.

5. **Interpretation of “New Knowledge”**  
   The manuscript argues that the suffix‑conditioned teacher provides “more new knowledge (thinking patterns)” to the student, supported by the Overlap Top‑K metric (Figure 3). While the metric shows reduced overlap relative to an AR‑style baseline, the causal link between lower overlap and richer knowledge transfer is not rigorously established. A qualitative analysis of the transferred patterns or an ablation that directly measures knowledge diversity would strengthen this claim.

Overall, the paper’s methodological contributions are sound, but the narrative occasionally stretches beyond the empirical support. Addressing the points above will align the claims with the presented data and improve the scientific rigor of the manuscript.
