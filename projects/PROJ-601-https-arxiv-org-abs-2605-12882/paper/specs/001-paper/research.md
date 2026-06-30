# Research Decisions & Rationale: CiteVQA Paper

## 1. Target Venue & Formatting
**Decision**: Target `arXiv` (Computer Science - Computation and Language / Artificial Intelligence).
**Rationale**: The paper is a reproduction and validation study. arXiv provides the fastest turnaround for benchmark validation and is the standard venue for pre-print reproducibility claims in MLLM research.
**LaTeX Class**: `arxiv-style` (specifically `arxiv` or `article` with `arxiv` class options).
**Version**: `article` class with `11pt` option, `a4paper`, and `twocolumn` layout to match standard arXiv submissions.

## 2. Figure Generation Toolkit
**Decision**: `matplotlib` (v3.8+) with `seaborn` (v0.13+) for statistical plotting.
**Rationale**:
- **Reproducibility**: Both libraries are pure Python (with C extensions) and run efficiently on CPU without GPU acceleration.
- **Precision**: They allow exact control over axis labels, legends, and data mapping required to visualize the `region_only_correct` vs. `answer_only_correct` breakdown.
- **Constraint**: `plotly` was rejected as it generates interactive HTML which is less suitable for static PDF submission and adds unnecessary dependency complexity for a reproduction paper.

## 3. Citation Management
**Decision**: `BibTeX` with `plainnat` bibliography style.
**Rationale**:
- **Verification**: The Reference-Validator has already verified the URLs for the core citations (CiteVQA original paper, Transformers library, WYSIATI literature).
- **Constraint**: No new citations will be introduced at this stage. The bibliography is strictly limited to the pre-validated list in `state/citations/`.
- **Style**: `plainnat` provides a standard, clean numeric citation style suitable for arXiv.

## 4. Metric Definition & Validation
**Decision**: Strict adherence to the `SAA` (Strict Attributed Accuracy) formula defined in the CiteVQA paper, with an explicit `IoU` threshold of `0.5`.
**Rationale**:
- **Claim Support**: Claim 1 ("Standard accuracy fails...") requires a direct comparison between "Standard Accuracy" (Answer Correctness only) and "SAA" (Answer + Region).
- **Edge Case Handling**: The `eval/run.py` script must explicitly handle bounding boxes outside the `[0,1]` range by clamping or rejecting them, logging these as "Format Error" to prevent mathematical invalidity in the SAA calculation.
- **Transparency**: The `data-model.md` will explicitly bind the `IoU` threshold parameter to the code configuration.

## 5. Randomness & Determinism
**Decision**: Fix `random.seed`, `numpy.random.seed`, and `torch.manual_seed` to `42` (or the specific seed used in the research phase) for all inference runs.
**Rationale**:
- **Reproducibility**: To satisfy SC-001 (Reproducibility Success), the SAA score must be reproducible within ±0.01.
- **Limitation**: The paper will explicitly acknowledge that floating-point variations on different CPU architectures may cause minor deviations, but the fixed seed ensures the *logic* of the pipeline is deterministic.

## 6. Data Integrity Strategy
**Decision**: Pre-filtering via `data/validate_dataset.py` before inference.
**Rationale**:
- **Claim Support**: Claim 3 ("Roughly X% are hallucinations") relies on a clean denominator. Including records with missing ground-truth boxes would skew the SAA calculation.
- **Transparency**: The `skipped_count` and reasons (e.g., `missing_bbox`, `missing_image`) must be reported in the Results section to satisfy FR-003 and SC-003.