---
action_items:
- id: 1605ce7df13e
  severity: writing
  text: "The review focuses on the accuracy of factual claims and their alignment\
    \ with cited evidence. 1. Discrepancy in Performance Claims: The abstract and\
    \ introduction claim that pre-training on WildGUI yields \"consistent and substantial\
    \ improvements of 5\u201320% across multiple GUI grounding and action benchmarks.\"\
    \ However, the data presented in Table 1 (Grounding Benchmark) contradicts this\
    \ specific range. For instance, on the ScreenSpot-Pro benchmark, the Qwen2.5-VL-7B\
    \ model improves from a baseline of"
artifact_hash: 9b264bacebdc198566c55b892eadee81103ef77a0231b5f086f102e723db2633
artifact_path: projects/PROJ-616-video2gui-synthesizing-large-scale-inter/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-29T19:17:10.627231Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The review focuses on the accuracy of factual claims and their alignment with cited evidence.

**1. Discrepancy in Performance Claims:**
The abstract and introduction claim that pre-training on WildGUI yields "consistent and substantial improvements of 5–20% across multiple GUI grounding and action benchmarks." However, the data presented in Table 1 (Grounding Benchmark) contradicts this specific range. For instance, on the ScreenSpot-Pro benchmark, the Qwen2.5-VL-7B model improves from a baseline of 26.8 to 41.9, which is a **56.3% relative increase**. Similarly, Mimo-VL-7B improves from 41.2 to 56.9, a **38.1% increase**. While the improvements are indeed substantial, the specific "5–20%" range cited in the text appears to be factually inconsistent with the provided table data, potentially understating the results or referring to a different metric not clearly defined. This requires clarification or correction to ensure the claim accurately reflects the evidence.

**2. Unsubstantiated Verification Metrics:**
In Section 3.2 (Action Spatial Grounding), the authors state: "Manual verification of 200 randomly sampled actions confirms that over 95% are accurately parameterized." This is a strong quantitative claim. However, the paper fails to define the ground truth criteria used for this verification (e.g., Intersection over Union threshold for bounding boxes, pixel error tolerance for coordinates). Without a defined metric or a reference to a specific evaluation protocol in the Appendix, the "95%" figure is unverifiable. The claim of "accurately parameterized" is ambiguous without these definitions.

**3. Citation and Model Version Mismatch:**
Throughout the text (e.g., Section 3.1, 3.2, Appendix), the authors repeatedly cite "Gemini-3-Pro" as the annotation model. However, the corresponding bibliography entry `comanici2025gemini` is titled "Gemini 2.5: Pushing the frontier...". There is a clear discrepancy between the model version claimed in the text (3-Pro) and the version cited in the references (2.5). Unless "Gemini-3-Pro" is a known internal codename or a very recent release not yet reflected in the provided bibliography, this suggests a factual error in either the model name or the citation.

**4. Ambiguity in Dataset Statistics:**
The claim of spanning "over 1,500 applications and websites" (Abstract, Table 1) is supported by the "Environments" column in Table 1. However, the methodology for deriving this count is not explicitly detailed in the main text. It is unclear if this count is based on unique domain names, app package names, or a combination, and whether this count includes variations of the same application (e.g., different versions or localized versions). While likely accurate, the lack of a clear definition for "application" and "website" in the context of the 12.7M trajectories makes the precision of this claim difficult to verify solely from the text.

**Recommendation:**
The authors should correct the performance improvement range in the abstract/introduction to match the data in Table 1, define the accuracy metrics for the 95% verification claim, and resolve the discrepancy between the "Gemini-3-Pro" text and the "Gemini 2.5" citation.
