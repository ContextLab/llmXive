---
action_items:
- id: 392df8a4ee1d
  severity: science
  text: The claim of '8.75x fewer training iterations' (Abstract, Intro) relies on
    comparing 600K iterations of DAR against 1.75M of SiT. However, Table 1 shows
    SiT-Plus (752M params) trained for 1M iterations still underperforms DAR. The
    paper lacks a direct comparison of DAR vs. SiT at the *same* iteration count (e.g.,
    600K) to isolate the architectural gain from the training duration effect. Re-run
    or report the FID of the baseline SiT at 600K iterations to validate the convergence
    speed claim.
- id: 8ff3f2b1e610
  severity: science
  text: The diagnostic in Section 3 (Fig. 1) measures gradient decay and magnitude
    inflation at a single timestep (t=1.0). The central hypothesis is that these symptoms
    are time-varying. The evidence is insufficient without showing that these metrics
    (magnitude, gradient, redundancy) vary significantly across the full denoising
    trajectory (t=0 to t=1), not just at the start of the process.
- id: 67f56e98ec2c
  severity: science
  text: The chunk size ablation (Table 3) tests only S={1, 4, 8}. The theoretical
    derivation (Prop 1) suggests an optimal S* dependent on alpha. Without testing
    intermediate values (e.g., S=2, 3, 5, 6) or reporting the fitted alpha, the empirical
    validation of the 'U-shaped' cost function is weak. The claim that S=4 is the
    global optimum is not robustly supported by the sparse grid search.
artifact_hash: 7a4bc7e64a39662319f7490ada4c2be57d6c20dd18ca5f1225c2e0b697bf14b3
artifact_path: projects/PROJ-625-https-arxiv-org-abs-2605-20708/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T23:00:33.961996Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a compelling hypothesis regarding the limitations of standard residual connections in Diffusion Transformers (DiTs) and proposes Diffusion-Adaptive Routing (DAR) as a solution. The diagnostic analysis in Section 3 identifies three symptoms (magnitude inflation, gradient decay, redundancy) that motivate the method. However, the scientific evidence supporting the specific quantitative claims requires strengthening in three areas.

First, the claim of an "8.75x" reduction in training iterations (Abstract, Section 1) is derived by comparing the DAR model at 600K iterations against the baseline SiT at 1.75M iterations. While Table 1 shows that a wider baseline (SiT-Plus) at 1M iterations does not match DAR, this does not fully isolate the effect of the architecture from the effect of training longer. To robustly support the convergence speed claim, the authors must report the FID of the standard SiT baseline specifically at 600K iterations. If the baseline FID at 600K is significantly worse than 7.56, the speedup claim holds; if it is close, the gain is marginal. The current evidence conflates architectural efficiency with training duration.

Second, the diagnostic evidence in Section 3 (Fig. 1) is measured at a single timestep ($t=1.0$). The paper's core argument is that residual routing needs to be "timestep-adaptive" because the information flow requirements change as noise levels shift. Measuring the "symptoms" (magnitude inflation, gradient decay) only at the start of the denoising process ($t=1.0$) provides an incomplete picture. The authors should demonstrate that these symptoms vary systematically across the denoising trajectory (e.g., comparing $t=0.1, 0.5, 1.0$) to prove that the problem is indeed time-varying and that a static residual is insufficient throughout the process.

Third, the ablation study on chunk size (Table 3) is too sparse to validate the theoretical proposition (Prop 1) regarding the optimal chunk size $S^*$. The authors test only $S \in \{1, 4, 8\}$ and observe a U-shape. However, without testing intermediate values (e.g., $S=2, 3, 5, 6$) or reporting the fitted parameter $\alpha$ from the rate-distortion model, it is difficult to confirm that $S=4$ is the true global minimum rather than a local optimum or an artifact of the specific grid. A denser sweep or a fit of the theoretical curve to the empirical data is necessary to substantiate the claim that the U-shape is predicted by the model.

Finally, while the linear probe in Section 4.2 (Fig. 3) effectively demonstrates that timestep information is decodable from hidden states, the link between this decodability and the *necessity* of the dynamic query mechanism could be tighter. The paper assumes that because $t$ is decodable, the dynamic query is the optimal way to use it. An ablation comparing the dynamic query against a static query with *explicit* timestep injection (which is also tested but perhaps not as thoroughly isolated) would strengthen the causal link between the diagnostic and the specific architectural choice.
