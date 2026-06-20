---
action_items:
- id: 18a236a7c05d
  severity: science
  text: "The paper claims \u201Creal\u2011time interactive video world models\u201D\
    \ but only reports first\u2011frame latency on a single GPU; it does not provide\
    \ end\u2011to\u2011end interaction latency, frame\u2011rate during rollout, or\
    \ user\u2011perceived latency. This overstates the real\u2011time capability."
- id: bdd3ac748ae9
  severity: science
  text: "The claim that the framework is \u201Carchitecture\u2011general\u201D is\
    \ supported only by two backbones (Wan2.1 and HY1.5). No experiments on other\
    \ architectures (e.g., MMDiT, latent diffusion) are shown, making the generality\
    \ claim unsupported."
- id: 027e94a5fb95
  severity: science
  text: "The statement that \u201Cfew\u2011step AR models preserve camera\u2011controllable\
    \ generation\u201D is based solely on visual inspection of a single figure (Fig.\u202F\
    1). No quantitative metric (e.g., pose error, controllability score) or user study\
    \ is provided, so the preservation claim is not substantiated."
- id: 982bf6612142
  severity: writing
  text: "Batch\u2011size and training\u2011step ablations (Figs.\u202F2\u20114) are\
    \ presented without statistical variance or repeated runs, yet the paper draws\
    \ definitive conclusions about minimal batch size and step thresholds. This extrapolates\
    \ beyond the limited evidence."
- id: d5bd3d785fd7
  severity: writing
  text: "The limitations section is absent. The manuscript does not discuss failure\
    \ modes (e.g., degradation of visual quality after distillation, sensitivity to\
    \ camera\u2011trajectory noise, or scalability to longer videos), which is required\
    \ given the strong performance claims."
- id: f31b9de12732
  severity: science
  text: "Latency numbers in Table\u202F1 exclude VAE encoding/decoding time and only\
    \ measure the first frame. Claiming \u201Clow\u2011latency inference\u201D without\
    \ reporting total inference time per frame or memory footprint is misleading."
- id: 0f27b604e2ad
  severity: science
  text: "The paper suggests that the framework can adapt existing world models (e.g.,\
    \ HY\u2011WorldPlay) to new data distributions, yet no experiments or benchmarks\
    \ are provided to support this claim."
- id: 02e5f4f9e75a
  severity: writing
  text: "The abstract and introduction repeatedly assert that a \u201Cfull\u2011stack,\
    \ reproducible, extensible recipe\u201D is provided, but the repository link is\
    \ not evaluated for completeness (e.g., missing scripts for data preprocessing,\
    \ missing checkpoints for intermediate stages). This overstates reproducibility."
artifact_hash: 0ee056e55f4c06cb2eab61e5c44334fbdff8ec177adecd2d7f6251ef9b5e9f6a
artifact_path: projects/PROJ-642-minwm-a-full-stack-open-source-framework/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-20T04:32:47.372935Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The manuscript presents an ambitious pipeline (minWM) for converting bidirectional video diffusion models into camera‑controllable few‑step autoregressive generators. While the engineering effort is noteworthy, several claims extend beyond the evidence presented, constituting overreach.

1. **Real‑time claim** – The authors repeatedly describe the output as a “real‑time interactive video world model.” The only timing metric reported is first‑frame latency on a single A800 GPU, with VAE time omitted and no measurement of per‑frame generation speed during rollout. Real‑time interaction requires sustained low latency (e.g., ≥30 fps) and low end‑to‑end delay when a user changes the camera trajectory. Without these measurements, the claim is unsupported.

2. **Generality across architectures** – The paper states that the framework is “architecture‑general” and demonstrates it on two backbones (Wan2.1 and HY1.5). No experiments on other popular video diffusion families (e.g., latent diffusion, MMDiT variants, or transformer‑only models) are provided, nor is there an analysis of how the PRoPE injection interacts with different attention mechanisms. The claim of broad applicability is therefore speculative.

3. **Preservation of controllability** – The assertion that the few‑step AR model “preserves camera‑controllable generation” rests on a single visual example (Fig. 1). No quantitative evaluation (e.g., pose error, controllability score, or user study) is offered, and no comparison to the original bidirectional model’s controllability is made. This extrapolates from anecdotal evidence.

4. **Ablation robustness** – Batch‑size and training‑step ablations (Figs. 2‑4) are presented as definitive thresholds (e.g., batch ≥ 16 required). However, each ablation appears to be a single run without error bars or repeated trials. Drawing firm conclusions about minimal batch size or step count without statistical validation overstates the reliability of these findings.

5. **Missing limitations and failure analysis** – The manuscript lacks a dedicated limitations discussion. Potential failure modes—such as degradation of visual fidelity after distillation, sensitivity to noisy camera trajectories, or scalability to longer video lengths—are not addressed, despite the strong performance claims.

6. **Incomplete reproducibility** – Although a GitHub link is provided, the paper does not verify that all scripts (data construction, PRoPE injection, intermediate checkpoint handling) are present and functional. Claiming a “fully open‑source, reproducible recipe” without confirming the completeness of the repository is premature.

7. **Latency reporting scope** – Table 1 reports only first‑frame latency, explicitly excluding VAE encoding/decoding. For interactive use, total per‑frame latency (including encoder/decoder and any post‑processing) is critical. The omission leads to an over‑optimistic portrayal of latency improvements.

8. **Adaptation of existing world models** – The claim that minWM can adapt existing models like HY‑WorldPlay to new data distributions is not substantiated with experiments; no adaptation results or benchmarks are shown.

**Overall assessment:** The paper’s core idea is valuable, but the current manuscript overstates its contributions and generality. To align claims with evidence, the authors should (i) provide end‑to‑end interactive latency measurements, (ii) include quantitative controllability metrics, (iii) broaden architectural experiments or temper the generality claim, (iv) report statistical variance for ablations, (v) add a limitations section, and (vi) verify the completeness of the released codebase. Addressing these points will bring the paper’s claims into a defensible range.
