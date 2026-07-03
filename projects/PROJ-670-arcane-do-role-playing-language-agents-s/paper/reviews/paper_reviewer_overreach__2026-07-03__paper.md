---
action_items:
- id: 2d79476fecd8
  severity: writing
  text: The claim that the 'Arc' context mode outperforms all others 'especially on
    Out-of-World scenarios where retrieval fails' (Sec 4.3) overstates the evidence.
    The paper does not explicitly demonstrate that RAG fails on these specific probes;
    it only shows Arc is better. The authors must clarify if RAG failure is a measured
    phenomenon or an assumption, and avoid implying causality without direct evidence
    of retrieval breakdown.
- id: 6ed4ce094836
  severity: writing
  text: The conclusion that DPO training 'specifically improves In-World and Out-of-World
    performance' (Sec 4.4) is an over-interpretation of the aggregate lift. The data
    shows a general lift across all categories. The authors should avoid attributing
    the gain specifically to 'trajectory direction' in out-of-text scenarios without
    a targeted ablation showing that SFT models fail specifically on trajectory direction
    in those specific scenarios, rather than just general fidelity.
- id: 0030340fac6f
  severity: writing
  text: The assertion that 'retrieval fails' on Out-of-World probes (Sec 4.3) is a
    strong claim that requires validation. The paper defines Out-of-World as 'non-source
    era' but does not provide data showing that RAG systems actually retrieve irrelevant
    or zero-shot results for these specific prompts. The authors should either provide
    evidence of retrieval failure or rephrase the claim to 'where retrieval is less
    likely to be directly applicable' to avoid overreach.
artifact_hash: 571d3401a83d0a75eab9bacc6292347c4c0034a87d0b29427ea4178c11f1a6c3
artifact_path: projects/PROJ-670-arcane-do-role-playing-language-agents-s/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T02:14:29.663197Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several strong claims regarding the superiority of the "Arc" context mode and the specific benefits of DPO training, particularly in "Out-of-World" scenarios. However, the evidence provided in the text and tables does not fully support the causal or mechanistic explanations offered in the narrative.

First, in Section 4.3 (Main Results), the authors state: "The advantage is largest on Out-of-World probes (+7.7 for DeepSeek-V4-Pro) where retrieval fails." This phrasing implies that the performance gap exists *because* retrieval fails. However, the paper does not present data quantifying the failure rate of the RAG baseline on these specific Out-of-World probes. While it is logically probable that RAG struggles with non-existent source text, the paper treats this as a measured fact rather than a hypothesis. The claim overreaches by presenting an assumption about the RAG mechanism as an empirical finding. The authors should either provide a retrieval success/failure analysis for these probes or soften the language to "where retrieval is less applicable."

Second, in Section 4.4 (Additional Results) and the Conclusion, the authors claim that DPO training "specifically improves In-World and Out-of-World performance" and that "DPO improves trajectory direction; SFT often holds a static voice." While Table 1 and Table 2 show that the DPO-tuned models have higher scores than SFT models, the lift is observed across *all* categories (In-Scenario, In-World, Out-of-World). The text selectively highlights the Out-of-World gain to support the narrative of "trajectory" improvement, but the data does not isolate "trajectory direction" as the specific variable that improved more in Out-of-World scenarios compared to In-Scenario scenarios. The claim that DPO *specifically* targets these out-of-text scenarios is an over-interpretation of a general performance lift. The authors should clarify that the improvement is general, or provide a specific analysis showing that the *magnitude* of improvement for trajectory direction is significantly higher in Out-of-World scenarios than in In-Scenario ones.

Finally, the claim in the Introduction that prior work "fails to assess behavioral shifts in scenarios beyond the source text" is slightly overstated. While TimeCHARA focuses on point-in-time knowledge, the paper does not explicitly rule out that other benchmarks might have incidental coverage of behavioral shifts, even if not their primary focus. A more precise claim would be that prior work does not *systematically* evaluate these shifts across a defined character arc.

These issues are primarily matters of precise wording and avoiding causal overreach rather than fundamental flaws in the experimental design. The data supports the general conclusion that Arc is effective, but the specific mechanistic explanations for *why* it works best in Out-of-World scenarios require more rigorous backing or softer phrasing.
