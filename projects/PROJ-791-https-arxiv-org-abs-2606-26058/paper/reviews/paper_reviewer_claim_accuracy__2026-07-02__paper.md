---
action_items:
- id: 6357fe6699ed
  severity: writing
  text: The '18.7% improvement' claim (Intro/Abstract) compares against Kling 1.6
    (0.725) but implies comparison against all SOTA baselines. The best open-source
    baseline (VACE) is 0.538, yielding a 60% gain. Explicitly state the baseline used
    for this percentage to avoid misleading readers.
- id: 19669ee8ab7e
  severity: writing
  text: Citations for 'GPT-5.2' and 'Qwen3-VL-8B' (Sec 4) refer to unreleased or non-existent
    models. Evaluation metrics relying on these models are unverifiable. Replace with
    publicly available model versions or clarify their status to ensure reproducibility.
- id: 319eedd3bcb4
  severity: writing
  text: The claim that edited videos are '3.3% of total data' (Sec 3.4) is mathematically
    correct (25k/750k) but ambiguous. Clarify that this refers to the total 750k dataset,
    not the Ditto-1M subset, to prevent misinterpretation of the training data composition.
artifact_hash: 94f10ea6969d9a855608669bc738975c27d93327dc527ce8f35f4b9e47a4390d
artifact_path: projects/PROJ-791-https-arxiv-org-abs-2606-26058/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T13:43:39.988579Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

This review focuses on the factual accuracy of claims and the validity of citations.

**1. Misleading Statistical Claim**
The manuscript repeatedly claims an "18.7% improvement in Cross-Domain Score over SOTA methods" (Abstract, Introduction, Section 4). A check of Table 1 reveals this figure is derived specifically by comparing the proposed method (0.861) against **Kling 1.6** (0.725). However, the text implies a comparison against the general set of SOTA methods. The best open-source baseline, VACE-Wan2.1, scores 0.538, meaning the actual improvement over that baseline is approximately 60%. By omitting the specific baseline used for the 18.7% figure, the claim is misleading. The authors must explicitly state "compared to Kling 1.6" or provide a more representative aggregate metric.

**2. Unverifiable Evaluation Models**
In Section 4, the authors cite **GPT-5.2** and **Qwen3-VL-8B** as the models used to compute the CD-Score and Qwen-Score. As of the current date, neither GPT-5.2 nor Qwen3 are publicly released or standard benchmarks. Citing unreleased or hypothetical models as the ground truth for evaluation undermines the reproducibility and factual validity of the experimental results. The authors must verify these model names, replace them with actual available versions (e.g., GPT-4o, Qwen2.5), or clarify if these are internal placeholders.

**3. Ambiguous Data Composition**
Section 3.4 states that edited videos account for "3.3% of the total data." While the math (25k edited pairs out of 750k total) is correct, the phrasing is ambiguous in the context of the Ditto-1M dataset discussion. It is unclear if the percentage refers to the total dataset or the specific Ditto subset (where it would be 50%). This ambiguity could lead readers to misinterpret the volume of editing data used for the Cross-Pair Consistent Loss. The sentence should be rephrased to explicitly define the denominator.

**4. Citation Validity**
The bibliography includes entries for `gpt52` and `bai2025qwen3`. If these refer to unreleased models, the citations are factually unsupported in the public domain. This casts doubt on the validity of the evaluation metrics derived from them.

These issues require correction to ensure the scientific claims are accurate, transparent, and reproducible.
