---
action_items:
- id: 06029be6a0a1
  severity: writing
  text: The paper relies heavily on external URLs for data and code access (e.g.,
    HuggingFace, GitHub, Project Page) defined via macros like \\benchmarkurl and
    \\codeurl. As this is an arXiv preprint, these links are prone to link rot. The
    authors must explicitly state the license (e.g., CC-BY, MIT) for the CaptureGuide-Dataset
    and ShutterMuse model in the text or a dedicated 'Data Availability' section,
    rather than assuming users will find it via a potentially unstable URL.
- id: 92a68737da81
  severity: science
  text: The dataset construction pipeline (EMDP and SGGP) utilizes third-party models
    (Nano-Banana-Pro, YOLO, Gemini-3.0-Pro) for data generation and verification.
    The paper does not specify the versioning or specific commit hashes of these external
    tools used during the data creation phase. Without version control for these dependencies,
    the reproducibility of the 130K sample dataset is compromised.
- id: 19e4065ee9b7
  severity: writing
  text: The schema for the subject-side guidance data is described as a triplet (scene,
    keypoints, rationales) with COCO-17 format. However, the paper does not provide
    a formal schema definition (e.g., JSON Schema or a detailed table of fields with
    types) for the dataset release. This lack of schema documentation makes it difficult
    for downstream users to parse the data correctly without reverse-engineering the
    code.
- id: 24ee94fa0b25
  severity: fatal
  text: The paper mentions using 'multiple online platforms' for image collection
    in the photographer-side seed set (Section 4.1) but does not provide a provenance
    log, a list of specific sources, or a statement regarding the copyright status
    of these images. This omission creates a significant legal and ethical risk for
    the dataset's public release.
artifact_hash: c05d947baccac31badb983e4672bc18e6d1ae08f6b2511780ab5cbcde805c567
artifact_path: projects/PROJ-789-shuttermuse-capture-time-photography-gui/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T22:09:40.294558Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The review focuses strictly on data quality, provenance, and reproducibility aspects of the manuscript.

**Data Provenance and Licensing:**
The manuscript introduces a large-scale dataset, **CaptureGuide-Dataset** (130K samples), and a benchmark, **CaptureGuide-Bench**. While the authors provide URLs for the dataset and code (e.g., `https://huggingface.co/datasets/ShutterMuse/CaptureGuide-Bench`), the paper lacks a dedicated section or explicit statement regarding the **license** under which this data is released. For a dataset of this size, especially one derived from "multiple online platforms" (Section 4.1), the absence of a clear license (e.g., CC-BY-4.0, MIT) and a detailed **provenance log** of the source images is a critical omission. The text mentions collecting images from online platforms but does not specify which platforms, nor does it address the copyright status of the source images. This creates a significant legal risk and hinders the dataset's utility for the broader community.

**Version Control and Reproducibility:**
The data construction pipelines (EMDP for photographer-side and SGGP for subject-side) rely heavily on external, third-party models: **Nano-Banana-Pro** for person removal, **YOLO-based pose estimators**, and **Gemini-3.0-Pro** for rationale generation and verification. The paper does not specify the **versions** or specific commit hashes of these external tools. Given that these models are likely to be updated or deprecated, the lack of version control makes the exact reproduction of the 130K sample dataset impossible. The authors must document the specific versions of all external dependencies used in the data generation pipeline.

**Schema and Data Structure:**
The paper describes the data schema for subject-side guidance as a triplet containing a scene image, 17 COCO keypoints, visibility states, and textual rationales. However, there is no formal **schema definition** (e.g., a JSON Schema or a detailed table specifying field types, constraints, and units) provided in the text or appendices. While the COCO format is standard, the specific handling of the "visibility" states (1, 0, -1) and the structure of the JSON output for the model training (Section 5) should be explicitly documented to ensure downstream users can correctly parse the data without ambiguity.

**Link Rot and External Dependencies:**
The manuscript relies on several external links for resources (Project Page, Benchmark, Model, Code). As an arXiv preprint, these links are susceptible to **link rot**. The authors should consider archiving the dataset and code in a permanent repository (e.g., Zenodo) with a DOI and explicitly citing that DOI in the paper, rather than relying solely on dynamic URLs that may change or become inaccessible.

**Recommendation:**
The paper requires a **minor revision** to address these data quality issues. Specifically, the authors must:
1.  Add a "Data Availability" section detailing the license, source provenance, and copyright status of the dataset.
2.  Provide version numbers for all external models used in the data construction pipeline.
3.  Include a formal schema definition for the dataset.
4.  Consider archiving the data with a persistent DOI.
