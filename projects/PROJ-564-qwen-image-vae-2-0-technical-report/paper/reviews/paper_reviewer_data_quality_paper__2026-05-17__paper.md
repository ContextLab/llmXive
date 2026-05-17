---
artifact_hash: 815458de8568b35ab5a02599bda9f602ed2dc04d545bca014bc4749f57af838e
artifact_path: projects/PROJ-564-qwen-image-vae-2-0-technical-report/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-05-17T14:50:14.853634Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

**Data Quality Review — Missing Provenance, Licensing, and Versioning**

This review focuses exclusively on data quality aspects: provenance, licensing, schema, missing-data handling, version control, and link rot of external sources. Several critical gaps require minor revision before publication.

**1. Training Data Provenance & Licensing (sec/data.tex, lines 1-15)**
The paper states training on "billions of images" covering "various categories, resolutions and aspect ratios" but provides **no license information**, **no source attribution**, and **no data card** for this corpus. Without explicit licensing (e.g., CC-BY, public domain, or commercial licenses), downstream users cannot legally reuse the model or verify compliance with data rights. This is a significant omission for a technical report claiming billion-scale training.

**2. Dataset Versioning (sec/experiment.tex, Table 1-2)**
Benchmarks ImageNet~\citep{deng2009imagenet} and FFHQ~\citep{Karras2018ASG} lack version specifications. ImageNet has multiple splits (e.g., 2012 validation, 2015 challenge); FFHQ has versions (e.g., 70k, 100k). Without version numbers, results cannot be reproduced. Similarly, OmniDocBench~\citep{Ouyang2024OmniDocBenchBD} requires a version tag or commit hash for the benchmark construction pipeline.

**3. Benchmark Construction Transparency (sec/bench.tex, lines 1-30)**
OmniDoc-TokenBench construction references OmniDocBench but omits:
- The exact version of OmniDocBench used
- License status of derived benchmark data
- Character count thresholds ([200, 600] for Chinese, [300, 600] for English) lack justification for reproducibility
- Human inspection criteria are qualitative ("blurred, visually redundant") without objective metrics

**4. External Link Stability (bibliography)**
Multiple GitHub URLs (e.g., `hunyuanimage2.1`, `flux2`) are subject to link rot. arXiv URLs are stable but should include access dates. Consider adding DOIs where available.

**5. Data Privacy & Consent**
No mention of privacy safeguards for the billion-scale corpus or human inspection of OmniDoc-TokenBench samples.

**Required Actions:**
- Add dataset licenses and sources for training corpus (sec/data.tex)
- Specify version numbers for all benchmark datasets (Table 1-2 captions)
- Provide a data card or datasheet link for OmniDoc-TokenBench
- Add access dates to external URLs in bibliography

These revisions are necessary for reproducibility and legal compliance without affecting technical claims.
