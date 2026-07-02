---
action_items:
- id: 622197541c01
  severity: science
  text: The claim that the refiner improves 'camera-control accuracy' (Tab. 1) lacks
    a mechanistic explanation. The refiner is trained on visual fidelity, yet pose
    error (RotErr) drops. Clarify if this is a side effect of better visual consistency
    aiding pose estimation or if the refiner explicitly optimizes geometry.
- id: 7af0083ef729
  severity: science
  text: "The 'Dual-Branch Camera Control' section claims the Pl\xFCcker branch restores\
    \ motion 'inside each VAE stride' (Sec 3.3), yet it is added as a residual after\
    \ self-attention. Explain how a block-wise addition to latent tokens recovers\
    \ high-frequency motion discarded by VAE temporal downsampling."
- id: 3705cc02d0a6
  severity: science
  text: The GDN key scaling ablation (Fig 5) asserts $1/\sqrt{D \cdot S}$ prevents
    matrix expansion but lacks a derivation. Justify why this specific scaling ensures
    the spectral radius of the transition matrix remains $\le 1$ for all gate values
    and key distributions.
artifact_hash: e5cefeb8f5a622284bf4bd8a2b4800bf995401cb7708f8533b8b272aa0c905d4
artifact_path: projects/PROJ-576-sana-wm-efficient-minute-scale-world-mod/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:44:01.919205Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The paper presents a coherent architecture for minute-scale world modeling, but several causal links between proposed mechanisms and reported outcomes require clarification to ensure logical consistency.

First, the claim that the **Second-Stage Refiner** improves **camera-control accuracy** (Table 1 and Appendix Table A1 show reduced RotErr/TransErr for the refined model) is not logically supported by the described mechanism. The refiner is trained via truncated-$\sigma$ flow matching to map noisy latents to high-fidelity targets, conditioned on text and camera poses. While this improves visual quality (VBench scores), the text does not explain *how* a visual refinement process reduces geometric pose error. If the Stage-1 model already generates a video with a specific camera trajectory, a visual refiner should ideally preserve that trajectory while sharpening details. A reduction in pose error suggests the Stage-1 model's trajectory estimation (via Pi3X) was biased by visual artifacts, or the refiner implicitly corrects geometric drift. The authors must explicitly state whether the pose improvement is a secondary effect of reduced visual noise (making pose estimation more accurate) or if the refiner actively optimizes for geometric consistency. Without this distinction, the causal claim that the refiner "improves action following" is ambiguous.

Second, the **Dual-Branch Camera Control** mechanism (Sec 3.3) asserts that the Plücker mixing branch restores fine motion "inside each VAE stride." The text describes this branch as a "zero-initialized per-block projection" added "immediately after each self-attention output." Logically, adding a residual vector to the transformer output at the latent frame rate cannot recover high-frequency motion that was discarded by the VAE's temporal downsampling (which aggregates 8 raw frames into 1 latent). If the VAE has already compressed the temporal resolution, the transformer output operates at the lower resolution. The text implies the Plücker branch operates at the "raw-frame" rate, but the implementation description places it as a block-wise addition to the latent stream. The authors need to clarify the signal flow: does the Plücker branch modulate the latent tokens to *predict* high-frequency details, or is there a separate upsampling step where this information is injected? The current description creates a logical gap between the "raw-frame" claim and the "block-wise addition" implementation.

Third, the **GDN Key Scaling** ablation (Fig 5) claims that unscaled keys lead to an expansive transition matrix $\mathbf{M}_t$, causing instability. The proposed fix scales keys by $1/\sqrt{D \cdot S}$. The logic relies on the trace of the key outer product being bounded. However, the text states $\operatorname{tr}(\mathbf{A}_t) \le 1$ implies $\|\mathbf{M}_t\|_2 \le \gamma_t \le 1$. This assumes the spectral norm is bounded by the trace, which is true for positive semidefinite matrices, but the derivation assumes the gates $\beta$ and normalized keys behave in a way that strictly satisfies this bound under all training dynamics. The paper asserts this scaling "ensures stable convergence" without providing the mathematical bound or counter-example for why $1/\sqrt{D}$ (standard token-wise scaling) fails specifically for the frame-wise aggregation of $S$ tokens. A brief derivation or citation of the spectral bound for this specific frame-wise aggregation would strengthen the logical consistency of this design choice.
