---
action_items: []
artifact_hash: 0fd8fa2b8ede4e304df4503c08bd0823fb3038495b7a89b759c4ee4216df60db
artifact_path: projects/PROJ-731-zone-of-proximal-policy-optimization-tea/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-23T13:02:22.315354Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.5
verdict: accept
---

The manuscript presents a coherent logical chain from problem definition to proposed solution and empirical validation. Below I outline the key logical checkpoints and why they hold.

1. **Problem framing (Sec. 1 & 2)** – The authors correctly identify two failure modes of conventional knowledge distillation: (i) logit‑matching over‑concentrates on teacher peaks, and (ii) inserting teacher logits into the policy gradient violates the on‑policy assumption. These premises are well‑cited (e.g., \citet{gou2021knowledge,ko2024distillm}) and set up a clear motivation for moving teacher information into the prompt rather than the gradient.

2. **Definition of “hard question” (Sec. 3.1)** – A hard question is defined as one whose within‑group mean rollout accuracy \(\bar r_x<0.5\). This threshold is explicitly used throughout the algorithm (e.g., buffer admission in Alg. 1) and aligns with the intuition that a 50 % success rate is the point at which the student is no longer “guessing”. No contradictory definition appears elsewhere.

3. **Construction of BCQ and NCQ (Sec. 3.1)** – The two prompt reformulations are logically exhaustive for hard questions: BCQ supplies a correct teacher candidate and a wrong student candidate, while NCQ aggregates all wrong student candidates. The manuscript acknowledges the edge case where the teacher also fails (Limitation § 6.1) and explicitly states that NCQ alone is used then, preserving internal consistency.

4. **Preservation of on‑policy learning (Sec. 3.1 & Alg. 1)** – By feeding BCQ/NCQ prompts to the student policy \(\pi_\theta\) and never back‑propagating through teacher tokens, the gradient is computed solely on the student’s own token distribution. This directly satisfies the claim that ZPPO “keeps the teacher inside the prompt rather than the policy gradient”, and there is no hidden dependence on teacher gradients.

5. **Replay buffer logic (Sec. 3.2 & Alg. 1)** – The buffer admits only hard questions and evicts entries once \(\bar r_x\ge0.5\). The graduation rule is consistently applied in the description of Fig. 4 (hard‑question graduation rates) and the buffer dynamics plots (Fig. A‑3). No contradictory admission or eviction criteria are presented.

6. **Empirical support for causal claims** –  
   - **Macro‑average gains**: Table 1 (representative macro‑average) shows ZPPO improving from 25.2 % (Base) to 33.1 % (ZPPO) for LLM, a +7.9 pp increase, directly supporting the claim of “super‑additive” improvement over GRPO.  
   - **Scale‑dependent effect**: Table 2 (hint‑prefix comparison) reports a +9.3 pp lift for 0.8 B VLM benchmarks, matching the abstract’s “largest gains at the smallest scale”.  
   - **Component ablations**: Table 3 (ablation) demonstrates that replay alone (+0.5–+1.6 pp) and reformulations alone (+1.2–+1.8 pp) each improve performance, while their combination yields a larger boost (+2.8 pp), confirming the super‑additive claim.  
   - **Teacher‑scale analysis**: Fig. 5 (teacher‑scale) shows monotonic increase in Δ as teacher size grows, consistent with the textual claim that “larger teachers yield larger gains”.

7. **No internal contradictions** – All sections reference the same definitions (hard‑question threshold, buffer capacity, augmentation fractions). The limitations (§ 6) correctly qualify the earlier optimistic statements, e.g., acknowledging that BCQ is unavailable when the teacher fails, which does not undermine the earlier claim that “BCQ provides a correct teacher trace”.

8. **Statistical robustness** – The authors perform a 10 000‑sample cluster bootstrap (§ A‑9) and report 95 % CIs that exclude zero for every reported Δ, reinforcing that the observed improvements are not due to random variation.

Overall, the logical flow from hypothesis to method to results is sound, and the causal claims are substantiated by the presented experiments and analyses. No contradictory statements or unsupported leaps are detected. The paper meets the logical‑consistency criteria for acceptance.
