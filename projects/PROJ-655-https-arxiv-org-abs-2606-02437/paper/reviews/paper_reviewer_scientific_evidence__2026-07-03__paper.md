---
action_items:
- id: 1ef1c110de06
  severity: science
  text: The claim that diversity among 198 LoRA variants yields a +0.0533 accuracy
    gain over repetition (Section 4.3) lacks statistical significance testing. Please
    report p-values or confidence intervals for the difference between the Collaboration
    and Repetition curves to rule out random variance.
- id: 9f948ded938f
  severity: science
  text: The 'DishNameBenchmark' capacity law (10^-3 to 10^-2 tokens/param) is presented
    as a sharp transition, but the experimental design (data permutation/masking)
    is not fully described. Clarify if the 'saturation' is due to interference or
    capacity limits, and provide the specific dataset size and composition used for
    this benchmark.
- id: 0b0633afab02
  severity: science
  text: The OLoRA-tail initialization results (Section 3.2.2) show a +11.5% gain on
    Qwen3-30B, but the baseline comparison uses a single seed or unspecified seed
    count for the standard LoRA degradation. Reproduce the low-rank (r=1) comparison
    with a larger seed count (e.g., n>=5) to confirm the stability claim is not an
    outlier.
- id: 77371b9ae089
  severity: science
  text: The trillion-scale Kimi K2 experiment (Section 2.3) claims a 10% compute footprint
    reduction but provides no error bars or variance metrics on the reward curves.
    Given the high variance typical of MoE RL, include standard deviation bands or
    multiple run averages to validate the stability of the Router Replay R3 fix.
artifact_hash: 98f7fcdee505c1b0d734c7251a396631b218366acf62d66b7a26c51efa8d758b
artifact_path: projects/PROJ-655-https-arxiv-org-abs-2606-02437/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T08:40:43.165415Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a compelling three-axis framework for PEFT scaling, supported by a mix of theoretical arguments and empirical results. However, the strength of the scientific evidence is currently undermined by a lack of rigorous statistical validation in key claims and insufficient detail on experimental controls for high-variance regimes.

First, the central claim in Section 4.3 regarding "Diversity as a Source of Collective Intelligence" relies on a comparison between Collaboration (distinct LoRA variants) and Repetition (repeated sampling). The paper asserts a +0.0533 accuracy advantage for collaboration at k=198. While the trend is visually clear in Figure 4, the text does not report p-values, confidence intervals, or a statistical test (e.g., bootstrap or t-test) to confirm that this gain is statistically significant and not a result of random variance in the majority voting process. Without this, the claim that diversity provides a *computational* resource rather than just noise reduction remains speculative.

Second, the "DishNameBenchmark" results in Section 4.1 propose a sharp capacity law for LoRA memory (10^-3 to 10^-2 tokens/param). The evidence for this "sharp transition" is presented as a curve, but the experimental setup is opaque. Specifically, the method of "data permutation and masking" used to generate the variants is not detailed. It is unclear if the observed saturation is a true capacity limit of the adapter or an artifact of the specific data distribution or interference patterns in the benchmark. The paper needs to clarify the dataset size, the nature of the "slots" being written, and whether the linear drop post-saturation holds across different task types or is specific to the synthetic benchmark.

Third, the results for OLoRA-tail in Section 3.2.2 are promising, particularly the stability at rank r=1. However, the comparison against standard LoRA shows a dramatic degradation for the baseline (from +15% to -18%). The text mentions "6 random seeds" for the error bars in Figure 3.4, but it is not explicitly stated if the standard LoRA baseline was evaluated with the same rigorous seed count to ensure the degradation is a consistent failure mode and not a seed-specific anomaly. Given the high sensitivity of low-rank RL, a larger seed count (n>=5) for the baseline comparison is necessary to robustly support the claim that the failure is due to initialization geometry rather than optimization noise.

Finally, the trillion-scale MoE experiments (Section 2.3) are critical to the "Scale Up" argument. The claim that Router Replay R3 stabilizes training is supported by curves, but MoE RL is notoriously high-variance. The figures show single-run trajectories. To validate the robustness of the solution, the authors should provide error bands (standard deviation) across multiple runs or explicitly state the number of runs averaged. A single stable run does not prove the method is reliable at scale; it only proves it *can* work.

In summary, the paper's framework is sound, but the empirical evidence requires stronger statistical backing and more transparent experimental controls to support the specific quantitative claims made.
