---
action_items:
- id: b17e6c8fc5ac
  severity: writing
  text: "Temper the claim that Reflective Masking is a \u201Cfundamental primitive\u201D\
    \ for reasoning in MDMs; the current evidence is limited to three tasks and a\
    \ narrow set of baselines."
- id: 82f3d626b74f
  severity: science
  text: "Add stronger, state\u2011of\u2011the\u2011art baselines (e.g., recent mask\u2011\
    diffusion editing or revision methods) for image editing and Sudoku to substantiate\
    \ the reported gains."
- id: 18f7bdde0fc5
  severity: writing
  text: "Clarify that History Reference introduces a new input representation (accumulated\
    \ embedding with rotation) and incurs extra computation, which contradicts the\
    \ statement of \u201Cno architectural changes.\u201D"
- id: e299fd0a61c6
  severity: science
  text: Discuss the scalability of the method to larger diffusion models, as the limitations
    section admits that experiments are on relatively small models.
- id: 0a7f5e6733ae
  severity: science
  text: "Provide empirical analysis (e.g., ablation of the Bayes\u2011consistent training\
    \ objective) to support the theoretical claims about optimality under 0\u2011\
    1 revision risk."
artifact_hash: 7fece54febe808e7b8d966174edf071d45cfb2bebbcbdcb010a99fdaf0b84671
artifact_path: projects/PROJ-765-multi-turn-reflective-masking-elicits-re/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-23T10:22:07.623069Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The manuscript introduces Reflective Masking (RM) as a post‑training capability for mask diffusion models (MDMs) and proposes a History Reference (HR) mechanism to incorporate trajectory information. While the idea is interesting, several statements extend beyond what the presented data and analyses can justify.

1. **Over‑generalized claims** – The paper repeatedly positions RM as a “fundamental primitive” for reasoning in MDMs and suggests it opens a “promising direction” for all diffusion‑based generative reasoning. The empirical evaluation, however, is confined to three tasks (image editing, Sudoku, and a handful of text reasoning benchmarks) and compares against a limited set of baselines (primarily the authors’ own SFT variants). No comparison is made to recent state‑of‑the‑art mask‑diffusion editing or revision methods (e.g., RemeDi, Remasking, or other iterative refinement approaches). Consequently, the claim of broad superiority is not fully supported.

2. **“No architectural changes” assertion** – The HR component adds a per‑position accumulated embedding with rotary‑style rotations and a decay factor, which modifies the model’s input pipeline and introduces extra computation. This constitutes a non‑trivial architectural augmentation, contrary to the claim that the method requires “no architectural changes.” The manuscript should acknowledge this modification and discuss its computational overhead.

3. **Theoretical optimality vs. practical performance** – Theoretical sections (Theorems 1–3) prove Bayes‑consistency of the cross‑entropy loss under a “rich‑family” assumption. In practice, the models are far from the idealized class, and the paper does not provide empirical evidence that the learned policies approach the Bayes‑optimal risk. An ablation showing the impact of the loss design (e.g., comparing uniform vs. top‑k corruption proposals) would strengthen the link between theory and practice.

4. **Scalability and resource claims** – The authors highlight a 5‑hour training time on two H100 GPUs as a major advantage. While this is impressive for the modest models used (e.g., a 0.81 M‑parameter Sudoku model), the limitations section already notes that larger diffusion models may not benefit directly. A discussion of how RM and HR scale with model size, memory, and inference latency would temper the current over‑optimistic portrayal.

5. **Evaluation breadth** – For image editing, the paper reports dramatic gains (e.g., 99.73 % edit precision) but only against the base Lumina and a simple SFT fine‑tune. Including stronger baselines such as InstructPix2Pix, MagicBrush, or recent diffusion‑based editors would contextualize these improvements. Similarly, Sudoku results lack comparison to dedicated symbolic solvers or other diffusion‑based correction methods.

Overall, the contribution is promising, but the manuscript overstates its generality and under‑reports comparative baselines. Addressing the points above—especially by moderating language, clarifying the architectural impact of HR, and expanding experimental baselines—will make the claims more commensurate with the evidence.
