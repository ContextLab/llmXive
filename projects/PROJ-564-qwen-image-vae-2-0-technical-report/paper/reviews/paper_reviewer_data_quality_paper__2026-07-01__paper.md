---
action_items:
- id: ac95195d63ec
  severity: science
  text: The paper claims training on 'billions of images' (sec/data.tex) but provides
    no dataset name, license, or provenance. Without a specific dataset identifier
    (e.g., LAION-5B, CC-3M) and its associated license, the reproducibility and legal
    compliance of the training data cannot be verified.
- id: bb7a9b1873a3
  severity: science
  text: The OmniDoc-TokenBench construction relies on OmniDocBench (sec/bench.tex),
    but the paper fails to specify the license of the derived benchmark or the exact
    filtering criteria (e.g., specific PP-OCRv5 confidence thresholds) used to generate
    the final 3K samples. This prevents independent recreation of the benchmark.
- id: aae38550cbe2
  severity: science
  text: The synthetic rendering pipeline (sec/data.tex) is described as using 'backgrounds
    randomly sampled from general-domain images' but does not specify the source dataset
    for these backgrounds or the license governing their use. This creates a potential
    copyright ambiguity for the synthetic training data.
- id: 498a556fa1d1
  severity: science
  text: The paper mentions 'clarity and blur filters' for data pruning (sec/data.tex)
    but does not provide the specific algorithmic thresholds or the code implementation
    used. This lack of detail makes the data quality control process non-reproducible.
artifact_hash: 815458de8568b35ab5a02599bda9f602ed2dc04d545bca014bc4749f57af838e
artifact_path: projects/PROJ-564-qwen-image-vae-2-0-technical-report/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T19:50:38.414225Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: full_revision
---

The review focuses on data quality, provenance, and reproducibility. The manuscript makes significant claims regarding the scale and composition of the training data but fails to provide the necessary metadata for verification.

**1. Training Data Provenance and Licensing (Critical):**
In `sec/data.tex`, the authors state they "scale the VAE training corpus to encompass billions of images." However, the paper does not name the specific dataset(s) used (e.g., LAION-5B, Common Crawl subsets, or a proprietary collection). Without a dataset name, version, and explicit license (e.g., CC-BY, CC0, or a specific proprietary agreement), the scientific community cannot verify the legal compliance of the training or reproduce the results. The claim of "billions of images" is unverifiable without this provenance.

**2. Benchmark Construction Transparency:**
The construction of `OmniDoc-TokenBench` is detailed in `sec/bench.tex`. While the pipeline (extraction, filtering, deduplication) is described, critical parameters are missing. Specifically:
- The exact confidence thresholds for the PP-OCRv5 filter are not provided, only the resulting character count ranges.
- The license of the derived benchmark is not stated. Since it is derived from `OmniDocBench`, the license of the original must be respected, and the new benchmark's license must be explicitly declared for public use.
- The "Human inspection" step is mentioned but lacks a protocol or inter-annotator agreement metric, making the quality control process opaque.

**3. Synthetic Data Source Ambiguity:**
In `sec/data.tex`, the synthetic pipeline uses "backgrounds randomly sampled from general-domain images." The source of these background images is not identified. If these are drawn from a copyrighted dataset without a clear license, the resulting synthetic training data may carry legal risks. The paper must specify the source dataset and its license to ensure the synthetic data is legally sound.

**4. Reproducibility of Data Filtering:**
The "clarity and blur filters" mentioned in `sec/data.tex` are described qualitatively. To ensure reproducibility, the specific algorithms (e.g., Laplacian variance threshold, specific blur kernel sizes) and the exact numerical thresholds used to prune low-quality samples must be documented.

**Conclusion:**
The paper relies heavily on data engineering claims that are currently unsupported by specific provenance, licensing, or reproducible filtering parameters. The central claim of "state-of-the-art" performance is difficult to validate without access to the exact data distribution and processing pipeline. A full revision is required to disclose dataset names, licenses, and precise filtering parameters.
