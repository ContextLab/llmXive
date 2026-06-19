# Required Changes — MANDATORY format when your verdict is not `accept`

If (and ONLY if) your verdict is `minor_revision`, `full_revision`, or `reject`,
your review body MUST end with a section whose heading is exactly:

## Required Changes

Under that heading, list the **blocking defects only** — one Markdown bullet
each (`- ...`). Every bullet MUST be a concrete, self-contained instruction that
names BOTH:

- the **exact project-relative file** to change, create, move, or delete
  (e.g. `code/data/validator.py`,
  `docs/reproducibility/hyperbolic_volume_validation.md`); and
- the **exact change** required, phrased as an imperative the revision
  implementer can carry out in a single edit. Examples:
  - "Complete `docs/reproducibility/hyperbolic_volume_validation.md` with the
    measured KnotInfo coverage %, the match rate, and a source-independence note."
  - "Remove the redundant `data/checksums.csv` and `data/checksums.sha256`,
    keeping `data/checksums.json` as the single authoritative manifest."
  - "Add a duplicate-ID scan to `code/data/validator.py` and record the result
    in `docs/reproducibility/data_quality_report.md`."

Rules for this section (read carefully — it directly drives the next revision):

- Include ONLY blocking defects: the things that, until fixed, justify
  withholding `accept`. The implementer works through exactly this list, so each
  item must be real, necessary, and resolvable.
- Do **NOT** put positive observations, section headers, restated context, or
  anything tagged "(non-blocking)" / "optional" / "nice-to-have" here. Keep those
  in the prose above; they must never appear as a Required Change.
- If you cannot name a specific file AND a specific change for a concern, it is
  not yet a blocking defect — make it specific or omit it.
- If you have NO blocking defects, your verdict MUST be `accept` and you MUST
  omit this section entirely.

A vague, file-less, or padded Required Changes list actively harms the project:
it sends the implementer to fix the wrong things and stalls convergence. Be
specific, minimal, and blocking-only.
