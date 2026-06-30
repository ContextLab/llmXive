---
action_items:
- id: 9da2fd4064ba
  severity: writing
  text: Are these models accessible via API? If so, the cost and rate limits for reproducing
    the benchmark should be disclosed.
- id: a86e98c83be0
  severity: writing
  text: If these models are hypothetical or future-dated, the evaluation results are
    unverifiable.
- id: 5d689c884a85
  severity: writing
  text: 'The use of closed-source judges introduces a "black box" bias that cannot
    be audited by the community. 2. Data Privacy and Synthetic Data Generation: The
    training data engine (Appendix, Section "Training Data Engine") constructs a 5.7M
    dataset by using GAR-8B and Qwen3-8B to generate captions for masks from SA-1B
    and COCONut.'
- id: bcdc3881e46f
  severity: writing
  text: SA-1B (Segment Anything) and COCONut contain images from the real world, which
    may include human faces, license plates, or other Personally Identifiable Information
    (PII).
- id: 0692021d443a
  severity: writing
  text: The paper does not explicitly state whether the source images were filtered
    for PII before caption generation.
- id: 5a35823bf04e
  severity: writing
  text: 'There is a risk that the DLM could memorize and regurgitate sensitive details
    from the source images if the synthetic captions are not carefully sanitized.
    The authors should confirm if a PII filtering step was applied to the source images
    or the generated captions. 3. Missing Ethics Statement: The main.tex file contains
    a commented-out Ethics Statement (lines 68-75). For a paper involving large-scale
    data processing and potential dual-use applications (e.g., automated surveillance,
    deepfake gen'
- id: d9e7e74aba23
  severity: writing
  text: The nature of the data used (human subjects, animals, etc.).
- id: 39b23b34b577
  severity: writing
  text: Potential misuse of the technology (e.g., enhancing surveillance capabilities).
artifact_hash: c2fe12c2ed011a24b223e04bd3ecaeef100189d2028034fd68b96cae705b806b
artifact_path: projects/PROJ-769-perceptiondlm-parallel-region-perception/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T17:19:29.296963Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The paper presents a novel approach to parallel region captioning using Diffusion Language Models (DLMs). From a safety and ethics perspective, the primary concerns revolve around data privacy, reproducibility of evaluation, and the lack of a formal ethics statement.

**1. Evaluation Reproducibility and Proprietary Models:**
In the Appendix (Section "Details of ParaDLC-Bench"), the authors state they use **GPT-5.2** and **Gemini-3.1-Pro** as LLM judges for evaluating the benchmark. The bibliography cites these as 2025 releases (`gpt5.2`, `gemini-2.5-pro`). As of the current date, these specific model versions are not publicly available or open-source. Relying on proprietary, closed-source, or non-existent models for the primary evaluation metric (ParaDLC-Bench scores) severely hinders reproducibility. The authors must clarify:
*   Are these models accessible via API? If so, the cost and rate limits for reproducing the benchmark should be disclosed.
*   If these models are hypothetical or future-dated, the evaluation results are unverifiable.
*   The use of closed-source judges introduces a "black box" bias that cannot be audited by the community.

**2. Data Privacy and Synthetic Data Generation:**
The training data engine (Appendix, Section "Training Data Engine") constructs a 5.7M dataset by using GAR-8B and Qwen3-8B to generate captions for masks from **SA-1B** and **COCONut**.
*   **SA-1B** (Segment Anything) and **COCONut** contain images from the real world, which may include human faces, license plates, or other Personally Identifiable Information (PII).
*   The paper does not explicitly state whether the source images were filtered for PII before caption generation.
*   There is a risk that the DLM could memorize and regurgitate sensitive details from the source images if the synthetic captions are not carefully sanitized. The authors should confirm if a PII filtering step was applied to the source images or the generated captions.

**3. Missing Ethics Statement:**
The `main.tex` file contains a commented-out Ethics Statement (lines 68-75). For a paper involving large-scale data processing and potential dual-use applications (e.g., automated surveillance, deepfake generation support via precise region description), a formal, uncommented Ethics Statement is mandatory. This statement should address:
*   The nature of the data used (human subjects, animals, etc.).
*   Potential misuse of the technology (e.g., enhancing surveillance capabilities).
*   Mitigation strategies employed (e.g., PII filtering, bias testing).

**4. Dual-Use Considerations:**
While the paper focuses on efficiency, the ability to generate detailed, parallel descriptions of multiple regions in an image could be misused for automated surveillance or targeted advertising. The authors should briefly discuss these potential dual-use risks in the conclusion or ethics section.

**Recommendation:**
The paper requires a **minor revision** to address these points. Specifically, the authors must uncomment and expand the Ethics Statement, clarify the status and accessibility of the judge models used for evaluation, and provide details on how PII was handled in the training data pipeline.
