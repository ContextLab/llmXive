---
action_items:
- id: 2d8caba89b50
  severity: science
  text: "The manuscript claims that APPO \u201Cmaintains behavior interpretability\u201D\
    \ but provides only limited qualitative evidence. Add systematic analysis (e.g.,\
    \ human evaluation of interpretability or explicit metrics) or temper the claim."
- id: 7c4da025b5e6
  severity: science
  text: "The theoretical section (Theorem\u202F2) presents a policy\u2011improvement\
    \ bound without clearly stating the required assumptions (e.g., exact KL constraints,\
    \ bounded rewards). Clarify the assumptions, their realism for large\u2011scale\
    \ LLM agents, and discuss any limitations of the bound."
- id: 3e2aca88a9b6
  severity: writing
  text: Impact statements assert broad societal value and safety compliance without
    any discussion of potential risks (e.g., misuse of more capable agents). Include
    a concise risk/ethics discussion or remove overstated impact claims.
- id: 9723b4a90341
  severity: science
  text: "Statistical significance of the reported gains (e.g., \u201Cnearly\u202F\
    4 points\u201D, \u201C+7.9\u202F%\u201D) is not provided. Report confidence intervals\
    \ or perform appropriate significance testing to substantiate performance improvements."
- id: 835f8b3ef2dc
  severity: writing
  text: The paper limits tool usage to Search and Python but claims generality of
    the method. Either broaden experiments to additional tool types or explicitly
    acknowledge that the results may not transfer to other tool sets.
artifact_hash: 3a43673385ee45c44ff0ac04e7e12a654dbb1cefe913b5676a26e486f2c9fad4
artifact_path: projects/PROJ-707-appo-agentic-procedural-policy-optimizat/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-17T21:18:37.351474Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper introduces APPO, an agentic reinforcement‑learning algorithm that shifts branching and credit‑assignment from coarse tool‑call units to fine‑grained “procedural” decision points. While the idea is promising, several claims extend beyond the presented evidence.

1. **Interpretability Claim (Section 1, Abstract, Conclusion).** The authors state that APPO “maintains behavior interpretability,” yet the only supporting material is a few visualizations of token selections (Figures 5‑6) and a qualitative case study. No systematic measure of interpretability (e.g., human judgments, explanation fidelity) is reported. This overstates the evidence; the claim should be qualified or backed by a dedicated evaluation.

2. **Theoretical Guarantees (Section 4.3, Theorems 1‑2).** Theorem 2 is presented as a policy‑improvement bound for APPO. However, the proof relies on strong assumptions (exact KL ≤ ε, bounded advantage scaling, occupancy matching) that are not discussed in the context of large language models with stochastic sampling and non‑stationary tool environments. The manuscript should explicitly list these assumptions, argue their plausibility, and acknowledge that the bound may not hold under realistic training dynamics.

3. **Broad Societal Impact (Appendix J).** The impact statement claims “extensive value to search systems, AI‑assisted healthcare and education” without any concrete analysis of how APPO would be deployed in those domains or what safety measures are required. This constitutes an overreach; a brief risk discussion or removal of the claim is advisable.

4. **Statistical Rigor of Empirical Gains.** Tables 1‑2 report average improvements (e.g., “+7.9 %”) but no confidence intervals, p‑values, or variance measures are provided. Given the modest absolute gains on some benchmarks and the variability inherent in RL training, statistical significance testing is needed to substantiate the claim of “consistent superiority.”

5. **Generality Across Tool Sets.** Experiments only involve Wikipedia search and a Python interpreter, yet the paper suggests that APPO is a generic improvement for agentic RL. The limitation is noted in Appendix G, but the main text does not reflect this. The authors should either broaden experiments to additional tools (e.g., web browsers, code execution environments) or clarify that the current results are confined to the evaluated tool set.

6. **Comparison with Stronger Baselines.** The baselines include ARPO and GIGPO, but newer tree‑search agents (e.g., MCTS‑DPO, SPORT) are omitted. Claiming “state‑of‑the‑art” performance without these comparisons may be premature.

Overall, the manuscript presents an interesting direction—fine‑grained branching based on a combined “Branching Score”—but several statements overstate the evidence. Addressing the points above will align the claims with the actual scope of the experiments and theoretical analysis.
