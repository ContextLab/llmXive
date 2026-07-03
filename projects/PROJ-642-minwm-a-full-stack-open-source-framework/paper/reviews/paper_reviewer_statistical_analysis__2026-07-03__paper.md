---
action_items:
- id: b4d573858074
  severity: science
  text: The ablation studies on training steps (Sec 4.3, Fig. 3) and batch size (Sec
    4.3, Fig. 4) rely entirely on qualitative visual inspection. To support the claim
    of 'strong controllability' or 'instability,' report quantitative metrics (e.g.,
    camera pose error RMSE, trajectory alignment scores) with confidence intervals
    or standard deviations across multiple seeds.
- id: 35f3c26b5aa9
  severity: science
  text: Latency results in Table 1 are reported as single point estimates without
    variance. Given the stochastic nature of GPU inference and potential system noise,
    report mean latency and standard deviation over multiple runs to validate the
    claimed speedup factors.
- id: 0b61b0315e7d
  severity: science
  text: The claim that batch size < 4 'often fails' (Sec 4.3) lacks statistical definition.
    Specify the failure rate (e.g., 0/5 seeds failed) and the criteria used to define
    'failure' to ensure reproducibility of the threshold.
artifact_hash: 0ee056e55f4c06cb2eab61e5c44334fbdff8ec177adecd2d7f6251ef9b5e9f6a
artifact_path: projects/PROJ-642-minwm-a-full-stack-open-source-framework/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T15:45:21.231165Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The manuscript presents a framework for converting video diffusion models into interactive world models. From a statistical analysis perspective, the primary concern is the lack of quantitative rigor in the ablation studies and performance reporting.

In Section 4.3 (Ablation Studies), the authors evaluate the effects of training steps (Fig. 3) and batch size (Fig. 4) on camera controllability. The conclusions drawn—such as the model being "completely uncontrollable" at 1-2k steps or "unstable" at batch size 8—are based entirely on qualitative visual inspection of generated video frames. Without quantitative metrics (e.g., Mean Squared Error between predicted and ground-truth camera trajectories, or a specific controllability score) and statistical measures of variance (e.g., results averaged over multiple random seeds with standard deviations), these claims are subjective and difficult to reproduce. The assertion that a batch size of 16 is the "minimum" for success requires a statistical definition of "success" and a failure rate analysis across seeds.

Furthermore, Table 1 reports first-frame latency as single point estimates (e.g., 3.446s). In systems research, latency is a stochastic variable influenced by GPU scheduling, memory bandwidth, and other factors. Reporting only the mean without standard deviation or confidence intervals makes it impossible to assess the reliability of the claimed $223.75\times$ speedup. A proper statistical treatment would involve running the inference multiple times (e.g., $N \ge 10$) and reporting the mean $\pm$ standard deviation to demonstrate that the observed speedup is statistically significant and not an artifact of a single favorable run.

Finally, the comparison between different data sources (SpatialVid vs. DL3DV vs. WorldPlay) in Section 4.3 relies on visual evidence. To substantiate the claim that "ground-truth camera poses are crucial," the authors should provide a quantitative comparison of the resulting model performance on a held-out test set using a standardized metric, rather than relying on qualitative descriptions of the generated videos.
