---
action_items:
- id: 3ac944b158d7
  severity: science
  text: Replace the MLLM-based evaluation metrics (MLLM-Score, Plausibility, Interaction,
    Aesthetics) with a rigorous human evaluation protocol or a calibrated geometric
    proxy. The current reliance on an MLLM judge (Gemini-3.0-Pro) to score the output
    of another MLLM (ShutterMuse) creates a circular validation loop that lacks scientific
    rigor for a benchmark paper.
- id: 09acdba861d5
  severity: science
  text: Address the 'floating feet' limitation in subject-side guidance. The paper
    admits the 17-keypoint COCO format fails to model foot-ground contact, causing
    visual artifacts. This is a scientific limitation of the representation, not a
    writing error. The authors must either collect a new dataset with denser foot
    keypoints (e.g., 21+ points) or propose a contact-aware pose representation to
    fix the underlying artifact.
- id: 5aa2172f8fe6
  severity: science
  text: Clarify the 'reject' decision logic in the photographer-side task. The current
    metrics (RSR) measure if the model says 'reject', but the paper does not define
    a ground-truth protocol for when an image is truly 'unsalvageable' versus just
    'poorly composed'. Without a clear definition of 'reject' ground truth, the RSR
    metric is scientifically ambiguous.
- id: 8d990176388c
  severity: writing
  text: The bibliography contains several citations with future dates (e.g., '2026',
    '2025' for models like GPT-5.5, Gemini-3.5). While this may be a placeholder for
    a future submission, it undermines the scientific credibility of the 'Related
    Work' and 'Experiments' sections. Verify all citation years and model versions
    against actual public releases or clearly mark them as 'pre-release' or 'hypothetical'
    if this is a simulation.
artifact_hash: c05d947baccac31badb983e4672bc18e6d1ae08f6b2511780ab5cbcde805c567
artifact_path: projects/PROJ-789-shuttermuse-capture-time-photography-gui/paper/metadata.json
backend: dartmouth
feedback: Evaluation metrics rely on MLLM judges without human-grounded calibration;
  subject-side pose visualization artifacts (floating feet) indicate a fundamental
  limitation in the 17-keypoint representation that requires new data collection or
  model architecture changes, not just text edits.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T22:03:08.281348Z'
reviewer_kind: llm
reviewer_name: paper_reviewer
score: 0.0
verdict: major_revision_science
---

# Free-form review body

## Strengths
- **Novel Problem Formulation:** The paper correctly identifies a gap in existing literature: the lack of "capture-time" guidance (deciding *whether* to shoot/refine/keep) versus the standard "post-hoc" cropping. The three-way decision framework (refine, keep, reject) is a valuable contribution to the field.
- **Unified Framework:** ShutterMuse successfully unifies photographer-side composition and subject-side pose recommendation into a single MLLM architecture, which is a practical and efficient design choice.
- **Dataset Scale:** The construction of a 130K-sample dataset (CaptureGuide-Dataset) with structured annotations is a significant resource for the community. The use of an expert-seeded, MLLM-verified self-distillation pipeline (EMDP) is a sophisticated approach to scaling annotation.
- **Efficiency:** The model demonstrates a substantial reduction in inference time compared to image-editing foundation models (4.96s vs 102s), making it viable for real-time capture assistance.

## Concerns
- **Circular Evaluation (Critical):** The most significant scientific flaw is the evaluation methodology. The paper uses an MLLM (Gemini-3.0-Pro) to judge the quality of the proposed model's (ShutterMuse) output. The prompt for the judge is extensive, but the validation relies entirely on the judge's internal "aesthetic" reasoning, which is not grounded in human preference data for the specific task. The user study (Section 6) is small (6 participants, 100 samples) and only validates the *ranking* correlation, not the absolute scores. A benchmark paper must establish a ground-truth metric that is independent of the model being evaluated.
- **Representation Limitation:** The paper explicitly acknowledges in the Appendix that the 17-keypoint COCO format causes "floating feet" artifacts because it lacks foot contact points. However, the paper proceeds to use this flawed representation for the subject-side task without proposing a solution (e.g., denser keypoints, contact maps). This is a fundamental scientific limitation that invalidates the "physical plausibility" claims for a significant portion of the data.
- **Ambiguous "Reject" Ground Truth:** The "reject" class is defined as images with "non-croppable defects." However, the paper does not provide a clear, objective protocol for annotators to distinguish between "poor composition" (which might be salvageable by a human) and "unsalvageable." This ambiguity makes the RSR (Reject Success Rate) metric difficult to interpret scientifically.
- **Citation Validity:** The bibliography lists several models with future dates (e.g., GPT-5.5, Gemini-3.5, Venus 2026). If this is a preprint for a future conference, these citations are speculative. If they are real, the dates are incorrect. This raises questions about the veracity of the experimental setup (e.g., did the authors actually run GPT-5.5?).

## Recommendation
The paper presents a compelling application and a large dataset, but the scientific rigor of the evaluation is insufficient for publication in its current form. The reliance on an MLLM judge to validate an MLLM's output without robust human-grounded calibration is a major flaw. Furthermore, the acknowledged failure of the 17-keypoint representation to model foot contact is a scientific limitation that cannot be fixed by text edits; it requires a change in the data representation or model architecture.

The authors must:
1.  **Re-evaluate the metrics:** Either conduct a larger, more rigorous human evaluation to ground the scores, or develop a geometric/physical proxy metric that does not rely on an MLLM judge.
2.  **Fix the pose representation:** Address the "floating feet" issue by either collecting a new dataset with denser keypoints or modifying the model to predict contact points.
3.  **Clarify the "reject" definition:** Provide a clear, objective definition and annotation protocol for the "reject" class.
4.  **Verify citations:** Ensure all cited models and dates are accurate and verifiable.

Given the need for new data collection or architectural changes to address the pose representation and the need for a fundamental re-think of the evaluation protocol, this requires a **major_revision_science**. The paper cannot be accepted or fixed with minor text edits.
