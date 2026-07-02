---
action_items:
- id: 6c82678f0b04
  severity: science
  text: The paper claims to use an 80K-video dataset sampled from OpenVid (src/4-Experiment.tex,
    Setup) but provides no license information, specific subset identifiers, or download
    scripts. Without a verifiable data manifest or license declaration, the provenance
    and legal usability of the training data cannot be confirmed.
- id: e18b0f4b4ebf
  severity: science
  text: The evaluation relies on VBench and VisionReward (src/4-Experiment.tex), but
    the paper does not specify the exact version of these benchmarks, the prompt lists
    used (beyond "100 prompts from Causal Forcing"), or the random seeds for evaluation.
    This lack of reproducibility metadata prevents independent verification of the
    reported scores.
- id: e0dda68979ff
  severity: science
  text: The latency and throughput metrics are measured on an A800 GPU (src/4-Experiment.tex),
    yet the paper does not disclose the specific hardware configuration (e.g., memory
    size, driver version, CUDA version) or whether the "ASD trick" (keeping first
    frame at 4 steps) was applied consistently across all compared baselines in the
    same environment. This makes the efficiency claims non-reproducible.
- id: 884c00d9fe7b
  severity: writing
  text: The paper references external GitHub repositories (thu-ml/Causal-Forcing,
    shengshu-ai/minWM) for code and data but does not include a data availability
    statement with specific commit hashes or version tags. If these links rot or the
    repositories are updated, the exact experimental setup described in the paper
    will become irreproducible.
artifact_hash: bc6ea3b7abb50e6d2d0c61521fe88f76d18733e7f3e4d74c5eba9d5fe9acb8e6
artifact_path: projects/PROJ-580-https-arxiv-org-abs-2605-15141/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T21:04:45.175289Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: full_revision
---

The paper fails to meet basic data quality standards regarding provenance, reproducibility, and version control. 

First, the training data provenance is opaque. Section 4.1 (Setup) states the use of an "80K dataset including videos sampled from OpenVid," but provides no license information, specific subset identifiers, or a data manifest. Without a clear statement of the data license (e.g., CC-BY, proprietary) and the exact sampling criteria, the legal and ethical validity of the dataset cannot be assessed. This is a critical omission for any paper claiming to train on large-scale video data.

Second, the evaluation protocol lacks necessary metadata for reproducibility. While the paper mentions using "100 prompts from Causal Forcing" for VBench and VisionReward, it does not provide the actual prompt list, the specific versions of the benchmark tools used, or the random seeds for the evaluation runs. The reported scores (e.g., VBench Total 84.14) are therefore not independently verifiable. Furthermore, the efficiency metrics (latency, throughput) are measured on an A800 GPU, but the specific hardware configuration (driver versions, CUDA toolkit) and the exact implementation details of the "ASD trick" for the baselines are not disclosed, making the performance comparison non-reproducible.

Finally, the paper relies on external links for code and data (e.g., `thu-ml/Causal-Forcing`) without providing commit hashes or version tags. This creates a risk of "link rot" or silent changes to the codebase, rendering the experimental results unrepeatable in the future. The authors must provide a data availability statement with specific versioning, license details, and a frozen snapshot of the code and data used for the experiments.
