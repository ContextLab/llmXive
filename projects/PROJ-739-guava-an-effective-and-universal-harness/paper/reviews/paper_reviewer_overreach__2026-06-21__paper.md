---
action_items:
- id: 9afbd163fa21
  severity: writing
  text: "Temper the claim that Guava is a \u201Cuniversal\u201D harness; the paper\
    \ only evaluates a limited set of models (GPT\u20115.4, Qwen\u20113.5\u20114B,\
    \ Gemini\u20113.1\u2011Pro, Claude\u2011Sonnet\u20114.6, and a 2B variant). Add\
    \ a discussion of this scope and avoid language suggesting applicability to all\
    \ future models."
- id: 5c363801ef45
  severity: science
  text: "Provide a more balanced assessment of generalization. The manuscript highlights\
    \ strong OOD performance, yet tasks such as *shell game* and *place all red objects\
    \ in basket* show very low success (\u2264\u202F6.7\u202F%). Include these failure\
    \ cases in the discussion and refrain from stating \u201Cstrong generalization\u201D\
    \ without qualifying the limitations."
- id: b2dc32dc6181
  severity: science
  text: "Report statistical significance (e.g., confidence intervals or hypothesis\
    \ tests) for the success\u2011rate comparisons in Tables\u202F1 and\u202F2. This\
    \ will substantiate the claim that the 4B model matches or exceeds proprietary\
    \ baselines rather than relying on point estimates from only 15 episodes per task."
artifact_hash: 305fa4e0caf5509b3ff951ed539855921f525d3dfdda7d54d245e51eb00f86f3
artifact_path: projects/PROJ-739-guava-an-effective-and-universal-harness/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-21T00:44:13.619722Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper presents an appealing framework (Guava) that combines iterative ReAct‑style loops, semantic tool abstractions, and multimodal observations. The experimental section demonstrates that a 4 B open‑source VLM, trained on fewer than 2 K simulated trajectories, can achieve overall success rates (75.6 %) that are numerically higher than the proprietary GPT‑5.4 baseline (70.2 %). However, several claims extend beyond what the presented data support.

1. **Universality of the Harness** – The manuscript repeatedly describes Guava as a “universal” or “model‑agnostic” interface (e.g., Abstract line 4, Introduction line 31, Conclusion line 2). Empirically, the study evaluates only a handful of models (GPT‑5.4, Qwen‑3.5‑4B, Gemini‑3.1‑Pro, Claude‑Sonnet‑4.6, and a 2 B variant). No systematic analysis is provided on how the harness scales with model size, modality, or architecture. Consequently, the universal claim is not justified by the evidence and risks over‑promising.

2. **Generalization Strength** – The authors assert “strong generalization to unseen objects, novel instructions, and long‑horizon tasks.” While OOD object and prompt tasks show respectable numbers (e.g., 100 % on *pick up carrot*), the long‑horizon OOD suite contains tasks where performance collapses (e.g., *shell game* 6.7 % for Guava‑Agent‑4B, *place all red objects in basket* 0 %). The paper does not discuss these failure modes, which undermines the blanket statement of strong generalization.

3. **Data‑Efficiency Claim** – The claim that “fewer than 2 K trajectories” suffice for “strong embodied capabilities” is plausible but not rigorously quantified. The success rates are reported as point estimates over 15 episodes per task, without confidence intervals or statistical tests. It is unclear whether the observed differences (e.g., 75.6 % vs. 70.2 %) are statistically significant or could arise from sampling variance.

4. **Real‑World Transfer** – Real‑world results (Fig. 5) are presented for only a subset of tasks (10 episodes each) and compared against the same baselines. The paper does not report variance across runs, nor does it discuss potential domain‑shift issues beyond the brief mention in the discussion. Claiming “comparable performance to SOTA proprietary models in zero‑shot real world setting” would be stronger if supported by statistical analysis and a broader task set.

5. **Tool‑Abstraction Benefits** – The ablation (Fig. 3) convincingly shows that semantic tools outperform low‑level primitives for the tested models. However, the paper extrapolates this to a design principle for all embodied agents without testing on models that lack strong tool‑calling abilities (e.g., the 2 B Qwen variant). A more cautious phrasing would acknowledge that the benefit may depend on the model’s instruction‑following and API‑use proficiency.

Overall, the manuscript’s core idea is solid, but the language overstates the breadth of the empirical support. Addressing the points above—especially by tempering universal claims, acknowledging failure cases, and providing statistical validation—will align the conclusions with the presented evidence.
