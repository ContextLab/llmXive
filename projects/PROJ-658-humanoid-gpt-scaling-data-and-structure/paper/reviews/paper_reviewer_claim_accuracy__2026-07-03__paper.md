---
action_items:
- id: f93392f79f7e
  severity: writing
  text: In the Introduction (Sec 1, 'Science of Scale'), the claim that the training
    set is 'over 200x larger than prior tracker training sets' is not supported by
    the provided data. Table 1 lists SONIC (2025) with 100M frames. 2B / 100M = 20x,
    not 200x. The 200x figure likely compares against older baselines (~7-10M frames)
    but is misleading when SONIC is explicitly cited as a related work in the same
    section and table. Clarify the baseline used for this comparison.
- id: 5bbdbe3c6a2a
  severity: writing
  text: In the Introduction (Sec 1, 'Science of Scale'), the paper claims to provide
    'the first systematic evidence that video-estimated motion can materially improve
    tracking.' However, the text does not cite a specific ablation study, figure,
    or table within the manuscript that isolates 'video-estimated motion' as a variable
    to prove this causal link. The claim appears to be an assertion without the immediate
    evidentiary support required for a 'first systematic evidence' statement.
- id: 492faf7b8394
  severity: writing
  text: 'In Section 4 (''Evaluation in Simulation''), the text states: ''even the
    best baseline (TCN-L at 56.15mm) lags behind Humanoid-GPT-S (43.25mm) by 30%.''
    However, Table 2 (tab:sim_scaling_backbone) does not contain a row for ''TCN-L''
    nor does it list MPKPE values of 56.15mm or 43.25mm. The table lists TCN (8-layer)
    with MPKPE 79.75mm. The specific numbers and the ''TCN-L'' variant mentioned in
    the text are missing from the provided tables, making the claim unverifiable from
    the current source.'
artifact_hash: 11a83a092083d485002512d3e56d130e02aef8501fdca7259786be2bc34086fd
artifact_path: projects/PROJ-658-humanoid-gpt-scaling-data-and-structure/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T13:26:59.756351Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The review focuses on the accuracy of factual claims and their alignment with the provided evidence (tables, text, and citations).

**1. Discrepancy in Scaling Claims (Introduction):**
In the "Science of Scale" paragraph (Introduction), the authors claim their 2B-frame corpus is "over 200x larger than prior tracker training sets." While this holds true when comparing against older datasets like AMASS (~7.2M frames), the paper explicitly cites and includes **SONIC** (2025) in Table 1 and the text as a related work that scales to **100M frames**. 
*   Calculation: 2,000M / 100M = 20x.
*   The claim of "200x" is factually incorrect relative to the most recent and relevant baseline (SONIC) presented in the same section. This exaggeration undermines the precision of the "Science of Scale" argument. The text should clarify that the 200x figure applies to *traditional* trackers (e.g., HumanPlus, OmniH2O) rather than the state-of-the-art scaling work (SONIC).

**2. Unsupported "First Systematic Evidence" Claim (Introduction):**
The Introduction states: "Crucially, we provide the first systematic evidence that *video-estimated motion* can materially improve tracking when the model and the training set are scaled appropriately."
*   **Issue:** The manuscript does not present a specific ablation study, figure, or table that isolates "video-estimated motion" as a variable to demonstrate this improvement. The data curation section mentions aggregating datasets (AMASS, MotionMillion, etc.) but does not explicitly detail a controlled experiment comparing "video-estimated" vs. "non-video" data within the 2B corpus to prove the causal link. Without a specific reference to a figure (e.g., "Fig. X") or a table row showing this specific comparison, the claim of "first systematic evidence" is unsupported by the provided text.

**3. Missing Data in Simulation Results (Section 4):**
In the "Results" paragraph of Section 4, the authors write: "even the best baseline (TCN-L at 56.15mm) lags behind Humanoid-GPT-S (43.25mm) by 30%."
*   **Issue:** Table 2 (`tab:sim_scaling_backbone`) lists a "TCN (8-layer)" with an MPKPE of **79.75mm**, not 56.15mm. Furthermore, there is no row labeled "TCN-L" in the table. The values 56.15mm and 43.25mm do not appear anywhere in the provided tables.
*   **Impact:** This suggests either a typo in the text, a missing table row, or a reference to data not included in the current manuscript version. The claim cannot be verified against the provided evidence, rendering the specific quantitative comparison invalid in its current form.

**4. Citation Consistency:**
The paper cites "SONIC" (2025) and "BeyondMimic" (2025) as existing works. While these are future-dated citations (likely arXiv preprints), the internal logic regarding their performance (e.g., SONIC's 100M frames) is consistent with the text, except for the scaling factor error noted in point #1.

**Conclusion:**
The paper makes strong claims about scaling and novelty that are currently undermined by numerical inconsistencies and missing supporting data in the text. The "200x" claim is mathematically inconsistent with the cited SONIC baseline, and the specific performance metrics for the "TCN-L" baseline are absent from the tables. These are writing-level fixes (correcting numbers and adding missing references) but are critical for the accuracy of the claims.
