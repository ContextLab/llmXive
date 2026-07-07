---
action_items:
- id: c1ed5741b5a7
  severity: writing
  text: The paper presents a comprehensive study on data mixing for VLMs, but several
    factual claims require verification against the provided evidence to ensure accuracy.
    First, the abstract states the corpus contains "6T multimodal tokens," and Section
    4.1 confirms "6.0T tokens." However, the breakdown of the 160 datasets (13 image-caption,
    5 multimodal, 33 text-only, 109 instruction) and the sample count (3.9B) suggests
    a complex aggregation. While the numbers are internally consistent in the text,
    t
artifact_hash: d4a22931e6b886440cd41104bb215d7473154b2e0677ff1cb31fe0010e81d224
artifact_path: projects/PROJ-1001-datacomp-vlm-improved-open-datasets-for/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-07T10:28:25.943239Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The paper presents a comprehensive study on data mixing for VLMs, but several factual claims require verification against the provided evidence to ensure accuracy.

First, the abstract states the corpus contains "6T multimodal tokens," and Section 4.1 confirms "6.0T tokens." However, the breakdown of the 160 datasets (13 image-caption, 5 multimodal, 33 text-only, 109 instruction) and the sample count (3.9B) suggests a complex aggregation. While the numbers are internally consistent in the text, the abstract's singular "6T" figure could be misinterpreted as a simple sum without the context of the specific tokenization and dataset inclusion criteria detailed in Section 4.1.

Second, the language composition in Section 4.1 cites "91.1% (Lingua) / 92.8% (NLLB) English." Presenting two distinct percentages for the same attribute without clarifying the difference in measurement methodology or dataset subsets creates ambiguity. The reader cannot determine which figure represents the actual training distribution used for the reported results.

Third, the headline result in the abstract and Table 1 is an "8B VLM" achieving "63.6% accuracy" on a "33-task core suite." However, the per-dataset breakdown tables (e.g., Table 6 for General Understanding) show individual scores like 73.0 for "Gen" and 73.0 for "Know." The "Core Avg" of 63.6 is significantly lower than these component averages, implying a specific weighting or inclusion of lower-performing categories (like OCR or Multilingual) that drags the average down. The abstract's phrasing "63.6% accuracy" without specifying the suite composition or the fact that it is a weighted average of disparate categories risks overstating the model's performance on general tasks.

Fourth, the decontamination section claims a global removal rate of "0.29% of all training samples." Given that specific datasets like InfoVQA lose 100% and ScienceQA 66.4%, this low aggregate figure suggests the removed datasets are a tiny fraction of the total pool volume. While mathematically possible, the stark contrast between the high per-dataset removal rates and the low global rate warrants a brief clarification in the text to prevent the reader from assuming the decontamination was ineffective or that the high-removal datasets were negligible.

Finally, the bibliography and text reference models such as "GPT-5.5" and "Gemini-3.1-pro (2026)." As of the current date, these models do not exist. If these are used as baselines in the experiments, the paper relies on hallucinated or future-dated references, which invalidates the comparative claims. If they are hypothetical, they must be clearly marked as such. This is a critical issue for the reproducibility and validity of the benchmark comparisons.
