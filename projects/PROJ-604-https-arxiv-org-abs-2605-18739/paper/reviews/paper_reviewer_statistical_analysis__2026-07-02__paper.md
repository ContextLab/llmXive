---
action_items:
- id: 6e8258dd173b
  severity: science
  text: "Table 1 (tab:wan22_ffn1_nvfp4) and Table 3 (tab:inference_progressive) report\
    \ single-point latency/FPS measurements without standard deviations, confidence\
    \ intervals, or sample sizes (N). Given the stochastic nature of video generation\
    \ and hardware variability, statistical significance of the reported speedups\
    \ (e.g., 2.15x) cannot be assessed. Please report mean \xB1 std dev over multiple\
    \ runs."
- id: a0e9c097bec6
  severity: science
  text: The VBench-Long results in Table 5 (tab:vbench_long_30s_60s) present mean
    scores but lack measures of variance (e.g., standard error) or statistical tests
    (e.g., t-tests) to validate the claim that LongLive-2.0 is 'significantly' better
    than baselines. Without variance estimates, the robustness of the ranking claims
    is unclear.
- id: f5d0d5adfb14
  severity: science
  text: The paper claims a '2.15x speedup' and '1.84x speedup' in the abstract and
    conclusion based on single measurements. These point estimates should be accompanied
    by confidence intervals or a statement on the number of trials performed to ensure
    reproducibility and statistical reliability of the performance gains.
artifact_hash: de9cc7b61426b053f14e2745d8dcacce77bcfbd73c84f2c8e9aae072a3bf9bd1
artifact_path: projects/PROJ-604-https-arxiv-org-abs-2605-18739/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T08:02:10.280154Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The paper presents a compelling system-level contribution to long video generation, focusing on NVFP4 quantization and sequence parallelism. However, from a statistical analysis perspective, the evaluation of performance gains lacks necessary rigor regarding variance and reproducibility.

The primary concern lies in the reporting of efficiency metrics. Tables 1, 3, and 4 (e.g., `tab:wan22_ffn1_nvfp4`, `tab:inference_progressive`) present single-point measurements for iteration time, end-to-end latency, and FPS. In systems research, especially involving GPU workloads with stochastic elements (like video generation sampling) and hardware variability, reporting a single run is insufficient to establish statistical significance. The authors claim specific speedups (e.g., "2.15x faster training") without providing standard deviations, confidence intervals, or the number of independent trials ($N$) used to derive these averages. Without this information, it is impossible to determine if the observed improvements are statistically significant or within the noise margin of the hardware environment.

Furthermore, the performance benchmarks on VBench and VBench-Long (Table 5, `tab:vbench_long_30s_60s`) report mean scores but omit measures of dispersion (e.g., standard deviation or standard error). The claim that LongLive-2.0 achieves the "best average rank" relies on these point estimates. To support the conclusion that the method is robustly superior, the authors should report the variance across different random seeds or prompt sets and, ideally, conduct statistical significance tests (such as paired t-tests) against the baselines.

Finally, the "Estimated" nature of the 64s results in Table 4 (Appendix, `tab:sp_inference_h100`) should be explicitly flagged with uncertainty bounds if derived from extrapolation, rather than presented as precise measurements. To meet the standards of rigorous statistical reporting, the authors must supplement their efficiency and quality tables with variance metrics and specify the experimental protocol (number of runs, seeds) used to generate the data.
