---
action_items:
- id: 2f236bdb3b01
  severity: writing
  text: Clarify Rex-Omni's coordinate representation in the Introduction (Lines 35-40)
    to align with Related Work (Lines 25-27), which describes it as 'point-based prediction'
    rather than box-coordinate token serialization.
- id: 6d17cee8bbf4
  severity: writing
  text: Harmonize dataset size reporting between the Abstract (138M), Section 3.4
    (138M), and Supplementary Table `query_stats` (~139.5M) for consistency.
artifact_hash: fd5c6b9375343e0bf1127bc6f967de79045e8b07b55446fb41fe382f0df7e34c
artifact_path: projects/PROJ-636-locateanything-fast-and-high-quality-vis/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-10T04:38:03.733493Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

This review focuses exclusively on the accuracy of factual claims and the validity of citations within the manuscript. Overall, the empirical claims regarding performance (F1 scores, throughput) are well-supported by the provided tables (e.g., Tab. `common_object_detection`, Tab. `gui_grounding`). However, there are inconsistencies in the characterization of baseline methodologies and dataset statistics that require correction to ensure factual precision.

First, there is a factual inconsistency regarding the baseline method **Rex-Omni**. In the Introduction (Lines 35-40), `jiang2025rexomni` is cited as an example of existing methods that "represent coordinates as either Textual Digits ... or Quantized Tokens (e.g., x1 -> y1 -> x2 -> y2)". This implies Rex-Omni serializes bounding box coordinates into a 1D token stream similar to Pix2Seq. However, in the Related Work section (Lines 25-27), the paper explicitly states, "Rex-Omni employs point-based prediction," and the method's title ("Detect Anything via Next Point Prediction") supports this. If Rex-Omni predicts points rather than box coordinates directly, grouping it under the "box-coordinate serialization" claim in the Introduction is inaccurate. This distinction is crucial for justifying the novelty of Parallel Box Decoding (PBD) versus point-based approaches. Please clarify whether Rex-Omni's evaluation involves converting points to boxes or if the Introduction claim should be refined to acknowledge point-based baselines separately.

Second, the reported dataset scale lacks consistency. The Abstract and Section 3.4 state the dataset contains "138 million training samples" or "138M natural language queries". However, the Supplementary Table `query_stats` (`tables/query_stats.tex`) lists the sum of queries across domains (Detection, GUI, Referring, OCR, Layout, Pointing) as approximately 139.5M (93.35 + 23.01 + 10.14 + 5.05 + 4.86 + 3.15). While minor, precise reporting is expected in large-scale dataset papers. Please align the text with the tabulated data (e.g., "approximately 139M queries").

Finally, the throughput claim of "2.5x faster than Rex-Omni" (Section 4.2) is mathematically accurate based on Table `common_object_detection` (12.7 BPS vs. 5.0 BPS), and the F1 improvements on LVIS and COCO (+3.8% and +1.8%) are also correctly calculated from the table data. These specific performance claims are valid. Addressing the methodological characterization and dataset size discrepancies will strengthen the paper's factual rigor.
