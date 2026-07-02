---
action_items:
- id: e4967dee7e5a
  severity: science
  text: The claim of '8.75x fewer iterations' to match 'converged quality' (Abstract)
    is unsupported. Table 1 shows the baseline improves significantly between 600K
    and 1.75M iterations. The paper does not prove DAR at 600K matches the baseline's
    final converged state, only its intermediate state.
- id: 9af3e6bd50a1
  severity: writing
  text: The claim that DAR 'preserves high-frequency details' in DMD (Abstract, Sec
    5.5) lacks evidence in the main text. The authors defer samples to the appendix
    without showing visual comparisons or quantitative metrics (e.g., LPIPS) to substantiate
    this specific qualitative claim.
- id: f2e034a4213e
  severity: writing
  text: The statement that diagnostic symptoms 'tighten in lockstep' with FID gains
    (Intro) overstates the evidence. The paper shows symptoms exist in the baseline
    and FID improves with DAR, but lacks a direct quantitative correlation analysis
    proving the reduction in symptoms tracks the FID improvement.
artifact_hash: 7a4bc7e64a39662319f7490ada4c2be57d6c20dd18ca5f1225c2e0b697bf14b3
artifact_path: projects/PROJ-625-https-arxiv-org-abs-2605-20708/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T22:59:53.856242Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several strong claims regarding the magnitude of performance gains and the causal mechanisms linking the proposed diagnosis to the solution, which appear to overreach the provided evidence.

First, the claim of an "8.75x fewer training iterations" to match the baseline's "converged quality" (Abstract, Section 1) is not fully supported. The authors compare their method at 600K iterations against the baseline at 1.75M iterations. However, Table 1 indicates that the baseline SiT model continues to improve significantly between 600K and 1.75M iterations (e.g., SDE FID drops from ~9.0 to 8.61). The paper fails to demonstrate that the DAR model at 600K actually reaches the *final* converged performance of the baseline at 1.75M, only that it reaches the baseline's performance at an intermediate, non-converged stage. This conflates "matching early-stage performance" with "matching converged performance," inflating the reported speedup.

Second, the claim that DAR "preserves high-frequency details" during Distribution Matching Distillation (DMD) on large-scale T2I models (Abstract, Section 5.5) is currently unsupported by quantitative or visual evidence in the main text. The authors state that "Full setup and samples are deferred to Appendix D," but the main text relies entirely on this assertion without presenting the actual generated images or metrics (such as LPIPS or spectral analysis) that would verify the preservation of high-frequency content. Without this evidence, the claim remains an overstatement of the results presented.

Finally, the statement that the identified diagnostic symptoms "tighten in lockstep with these FID gains" (Section 1) implies a direct, quantitative correlation between the reduction of the three symptoms (magnitude inflation, gradient decay, redundancy) and the FID improvement. While the paper shows the symptoms exist in the baseline and FID improves with DAR, it does not provide a rigorous analysis (e.g., a correlation plot or per-timestep breakdown) demonstrating that the *degree* of symptom reduction directly tracks the *degree* of FID improvement. This phrasing suggests a causal mechanism that is not explicitly proven by the data shown.
