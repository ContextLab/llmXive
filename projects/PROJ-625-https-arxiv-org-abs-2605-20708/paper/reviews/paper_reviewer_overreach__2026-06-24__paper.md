---
action_items:
- id: d1a727e458f8
  severity: writing
  text: "The manuscript claims to be the first systematic study of cross\u2011layer\
    \ information flow in Diffusion Transformers. Provide a more precise literature\
    \ context and acknowledge closely related works (e.g., U\u2011Net\u2011like skip\
    \ routing studies) to avoid overstating novelty."
- id: 7607f1ad00e4
  severity: writing
  text: "The statement that DAR is a \u201Cdrop\u2011in residual replacement\u201D\
    \ is not fully supported, as it introduces additional parameters, chunking logic,\
    \ and a new attention mechanism. Clarify the exact changes required to integrate\
    \ DAR into existing DiT codebases."
- id: 00b35f4e17a9
  severity: science
  text: The claim of orthogonality between DAR and REPA is based on limited experiments.
    Include a more thorough analysis (e.g., ablation of combined loss terms, statistical
    significance testing) to substantiate that the improvements truly compound rather
    than overlap.
- id: 053751ad429c
  severity: science
  text: "Performance gains are reported without detailed hyper\u2011parameter tuning\
    \ for the baselines. Ensure that baseline SiT/DiT models are optimally tuned (learning\
    \ rate schedules, regularization) to rule out that DAR\u2019s advantage stems\
    \ from unequal training settings."
- id: 1f333e499b77
  severity: writing
  text: "The paper asserts that DAR \u201Cpreserves the isotropic and homogeneous\
    \ Transformer stack,\u201D yet the depth\u2011wise attention fundamentally alters\
    \ the routing topology. Discuss any potential impact on model scaling properties\
    \ and compatibility with future architectural extensions."
- id: f48bf3b7e199
  severity: science
  text: "Provide quantitative evidence that the timestep\u2011aware routing variants\
    \ (static\u202F+\u202Ft\u2011injection, dynamic) are indeed necessary; the current\
    \ ablation (Table\u202F5) shows modest differences. Include statistical variance\
    \ or confidence intervals to demonstrate significance."
- id: 2ed218d350ae
  severity: science
  text: "The theoretical Proposition\u202F1 about chunk size optimality is based on\
    \ a simplified cost model. Validate the model empirically across a broader range\
    \ of depths (e.g., deeper DiTs) to confirm that the predicted S* aligns with observed\
    \ performance."
artifact_hash: 7a4bc7e64a39662319f7490ada4c2be57d6c20dd18ca5f1225c2e0b697bf14b3
artifact_path: projects/PROJ-625-https-arxiv-org-abs-2605-20708/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-24T18:00:33.514363Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper presents an interesting diagnostic of residual‑stream behavior in Diffusion Transformers (DiTs) and proposes a novel routing mechanism (DAR). However, several claims extend beyond what the presented evidence justifies, indicating over‑reach.

1. **Novelty Claim (Section 1, 3)** – The authors repeatedly state that this is the “first systematic study” of cross‑layer information flow in DiTs. While the diagnostic is thorough, prior works on U‑Net‑style skip connections and depth‑wise aggregation are closely related. The manuscript should contextualize these works more accurately to avoid overstating originality.

2. **Drop‑in Assertion (Section 3.2)** – DAR replaces the residual addition with a softmax‑weighted depth attention and introduces chunked aggregation. This adds learnable query vectors, per‑source RMSNorm, and a new memory‑efficient kernel. Claiming a “drop‑in” replacement without acknowledging these architectural and implementation changes misleads readers about integration effort.

3. **Orthogonality with REPA (Section 5.3, Table 6)** – The authors argue that DAR and REPA act on orthogonal axes and that their gains compound. The evidence consists of a single FID curve comparison. A more rigorous ablation (e.g., varying REPA weight, measuring gradient flow, statistical testing) is needed to substantiate true orthogonality rather than coincidental improvement.

4. **Baseline Fairness (Table 2, 4)** – The SiT and DiT baselines are trained with the same recipe, but the paper does not report any hyper‑parameter search for them. Since DAR introduces additional capacity (e.g., extra query parameters, chunk summaries), it is possible that part of the reported FID gain stems from unequal tuning. A fair comparison requires either hyper‑parameter sweeps for baselines or reporting that the same search budget was applied.

5. **Preservation of Homogeneity (Section 3.2)** – The claim that DAR “preserves the isotropic and homogeneous Transformer stack” conflicts with the introduction of a depth‑wise attention mechanism, which changes the routing topology. The authors should discuss any implications for model scaling, especially for deeper DiTs where the routing pattern may affect training dynamics.

6. **Timestep‑Awareness Impact (Table 5)** – The improvement from timestep‑aware queries over the static, timestep‑blind variant is modest (e.g., FID 22.36 → 17.39 at 100 K). Without confidence intervals or variance estimates, it is unclear whether this difference is statistically significant. Additional runs or a variance analysis would strengthen the claim that timestep awareness is essential.

7. **Theoretical Chunk‑Size Proposition (Proposition 1)** – The proposition provides a clean analytical optimum for chunk size under a simplified cost model. Yet the empirical validation is limited to three chunk sizes on a single depth (L = 56). Testing the prediction on deeper backbones (e.g., L > 100) would confirm that the model scales as expected.

Overall, the paper’s core ideas are promising, but the current presentation overstates novelty, integration simplicity, and the independence of its contributions. Addressing the points above will align the claims with the supporting evidence and improve the manuscript’s scientific rigor.
