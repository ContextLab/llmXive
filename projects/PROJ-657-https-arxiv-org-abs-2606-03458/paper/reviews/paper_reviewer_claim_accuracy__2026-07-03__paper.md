---
action_items:
- id: 315fe98e343a
  severity: writing
  text: The claim that KIVI 'underperform[s] in decode-heavy reasoning scenarios due
    to error accumulation' (Intro) is not supported by the provided tables. Table
    1 (AIME24/MATH500) and Table 3 (IF-Eval) show KIVI results are within 1-2% of
    FP16 and often comparable to other baselines, not a catastrophic failure. The
    text overstates the baseline's failure mode without citing a specific experiment
    showing KIVI collapse in long-horizon decoding.
- id: 01ac371d76df
  severity: writing
  text: The citation for the 'Needle-in-a-Haystack' benchmark (kamradt2023needle)
    is used to claim KIVI excels in prefill settings. However, the paper's own Figure
    NIAH (Appendix) and text suggest static NIAH is 'much easier' than the accumulated
    setting. The claim that KIVI 'excels' here needs to be qualified by the specific
    context (static vs. accumulated) to avoid misleading readers about its robustness
    in the proposed 'pseudo-decode' regime.
- id: 749bb7fa4cb6
  severity: writing
  text: The claim that 'top 5% errors cause most end-to-end degradation' (Key Ideas)
    is supported by Fig. outlier_impact (KL-divergence) but contradicted by the text
    in the Appendix ('Outlier Contributions to MSE') which states they cause a 'minority
    of MSE'. The paper conflates MSE (reconstruction error) with end-to-end quality
    (KL/accuracy) without clearly distinguishing that the 5% rule applies specifically
    to the impact on generation quality, not the raw error magnitude.
artifact_hash: 41b8c942a61f2cf7279ecdca15cbc48d6d8be293f3b82fe8c5a5b6e8c4e01484
artifact_path: projects/PROJ-657-https-arxiv-org-abs-2606-03458/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T01:17:47.968782Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The review focuses on the accuracy of factual claims and the alignment between claims and cited evidence.

**1. Overstated Baseline Performance Claims**
In the Introduction, the authors claim that methods like KIVI "underperform in decode-heavy reasoning scenarios due to error accumulation." While the paper proposes a method to mitigate this, the provided experimental tables (Tab. 1: AIME24/MATH500, Tab. 3: IFEval) do not support a claim of significant "underperformance" or "failure." KIVI achieves 55.5% vs 61.1% (FP16) on AIME24 and 77.8% vs 82.6% on MATH500. These are competitive results, not a collapse. The text implies a qualitative failure that the quantitative data does not fully substantiate. The claim should be tempered to reflect that KIVI shows *relative degradation* compared to the proposed method in long contexts, rather than a general inability to handle reasoning tasks.

**2. Conflation of MSE and End-to-End Quality**
The paper makes a central claim that "top 5% errors cause most end-to-end degradation" (Section Key Ideas, Fig. outlier_impact). This is supported by the KL-divergence analysis in the figure. However, the Appendix section "Outlier Contributions to MSE" explicitly states that these outliers contribute a "minority of MSE." The manuscript risks confusing readers by using the "5% rule" to justify the *magnitude* of the problem without clearly distinguishing that the *impact* (KL/accuracy) is disproportionate to the *magnitude* (MSE). The claim "outlier errors contribute disproportionally to end-to-end quality" is accurate, but the phrasing "cause most end-to-end degradation" without the "disproportionally" qualifier in the main text is slightly misleading when contrasted with the MSE data.

**3. Contextual Nuance in Benchmark Citations**
The Introduction cites `kamradt2023needle` to support the claim that KIVI "excels in prefill settings." The paper's own Appendix (Section NiaH) notes that "Static NiaH is easier than accumulated pseudo-decode." The claim that KIVI excels in NIAH is true for the static setting but potentially false for the accumulated setting the paper aims to solve. The text should clarify that KIVI's success is limited to *static* retrieval tasks, whereas the proposed method targets the *accumulated* error regime, to avoid implying KIVI fails at NIAH entirely.

**4. Citation Consistency**
The bibliography lists URLs for datasets (MATH500, AIME24, etc.) as "mismatch" in the metadata. While the paper text cites standard arXiv or GitHub links for these benchmarks (e.g., `lightman2024lets_math500`), the metadata flags suggest the provided citation keys in the LaTeX source might not resolve to the correct URLs in the final bibliography. This is a minor technical issue but affects the verifiability of the "standard benchmarks" claim.

Overall, the core scientific claim (variance normalization helps) is supported by the data, but the narrative framing of the baseline's failure and the distinction between error magnitude and quality impact requires tightening to match the evidence precisely.
