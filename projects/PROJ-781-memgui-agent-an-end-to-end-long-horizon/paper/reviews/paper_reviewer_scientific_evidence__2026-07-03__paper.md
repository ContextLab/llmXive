---
action_items:
- id: 230b27773a1e
  severity: science
  text: The ablation study (Table 3) presents component contributions (e.g., +35.0%
    P@1 for UI memory) but lacks statistical significance testing (e.g., p-values
    or confidence intervals). Given the small test set size (128 tasks), random variance
    could explain these gains. Please report significance tests or bootstrap CIs.
- id: dbd545b5ff1f
  severity: science
  text: The dataset construction relies on 'reasonableness filtering' of teacher rollouts
    (Sec 3.2, Appx D.3). The criteria for 'reasonable' are not quantified, and the
    filter rate is not reported. This introduces potential selection bias where only
    easy or obvious trajectories are retained, inflating SFT performance. Clarify
    the filtering protocol and report the rejection rate.
- id: bbf03de720db
  severity: science
  text: The claim that MemGUI-8B-SFT is the 'best open-data 8B model' (Sec 4.1) is
    based on a single benchmark (MemGUI-Bench) and MobileWorld. No comparison is made
    against other open-weight 8B models fine-tuned on similar data (e.g., UI-TARS,
    Mobile-Agent-V3 variants) on these specific long-horizon metrics. Broaden the
    baseline comparison to ensure the 'best' claim is robust.
artifact_hash: 7ba9201f0f49d9384a35f3eca07d4fd8d448c0da222a8a4e9472044b7e857c18
artifact_path: projects/PROJ-781-memgui-agent-an-end-to-end-long-horizon/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T19:23:45.511100Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The scientific evidence supporting the core claims of MemGUI-Agent is generally strong, particularly in the magnitude of performance gains observed on long-horizon tasks. The ablation study (Table 3) effectively isolates the contribution of the CONACT components, showing a substantial jump from 5.0% to 40.0% Pass@1 when adding UI memory actions and folding. The dataset construction (MemGUI-3K) appears rigorous, with a clear pipeline for expanding seed tasks and filtering teacher rollouts.

However, several aspects of the evidence require strengthening to rule out alternative explanations and ensure statistical robustness. First, the ablation results in Table 3 are presented as point estimates without measures of variance or statistical significance. With a test set of only 128 tasks (MemGUI-Bench), a 35% absolute gain is large, but without p-values or confidence intervals (e.g., via bootstrapping), it is difficult to rule out that the gains are due to random variance or specific task selection rather than the architectural change. The authors should report statistical significance for the key ablation comparisons.

Second, the "reasonableness filtering" step in the dataset construction (Section 3.2, Appendix D.3) is a potential source of selection bias. The paper states that teacher rollouts are filtered for "reasonableness" but does not define the criteria or report the rejection rate. If the filter disproportionately removes difficult or ambiguous trajectories, the resulting SFT dataset may be biased toward easier tasks, artificially inflating the performance of MemGUI-8B-SFT. The authors should clarify the filtering criteria and report the percentage of trajectories/steps rejected at this stage.

Finally, the claim that MemGUI-8B-SFT is the "best open-data 8B model" (Section 4.1) is currently supported only by comparisons against the base Qwen3-VL-8B-Instruct and a few proprietary frameworks. To substantiate this claim, the authors should include comparisons against other recent open-weight 8B models that have been fine-tuned for GUI tasks (e.g., UI-TARS, Mobile-Agent-V3 variants) on the same benchmarks. Without these baselines, the "best" claim remains relative to a limited set of competitors.
