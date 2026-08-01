# Lexicon Remediation Plan
**Date**: 2026-06-13
**Task ID**: T001e
**Context**: Remediation for Failed Lexicon Validation (Precision < 0.80)

## 1. Executive Summary
The automated hedge lexicon validation (Task T001d_exec) failed to meet the required precision threshold of 0.80 when compared against the human-annotated gold standard (`data/processed/hedge_gold_standard.csv`). This document outlines the specific steps to refine the lexicon, re-evaluate precision, and determine the final course of action.

## 2. Problem Diagnosis
Based on the validation logic defined in `src/analysis/validation.py`, the low precision indicates that the current lexicon is matching words that human raters did *not* identify as hedges (False Positives).

**Likely Causes:**
1. **Over-inclusion of Weak Modals:** Words like "should" or "could" are included but often function as advice rather than uncertainty markers in this specific dataset.
2. **Contextual Ambiguity:** The lexicon matches words regardless of context (e.g., "I think" as a hedge vs. "I think it's a cat" where the hedge is less relevant to the specific authenticity metric).
3. **Lexicon Drift:** The initial 15-word list may not align with the specific linguistic patterns of the `convai2` or `cornell-movie-dialogs` corpus used in T001f.

## 3. Remediation Steps

### Step 1: Lexicon Pruning (Immediate Action)
Review the `HEDGE_LEXICON` definition in `src/extraction/hedge_extractor.py`. Remove words that historically yield high false-positive rates in general dialogue corpora.
* **Action:** Remove "likely" and "unlikely" if they appear infrequently or are used in non-uncertainty contexts.
* **Action:** Review "seem" and "appear" for usage in descriptive rather than hedging contexts.

### Step 2: Contextual Refinement (If Pruning Fails)
If simple word removal reduces recall too much, implement a simple context window check in `src/analysis/validation.py`.
* **Action:** Modify `find_lexicon_matches` to only flag a match if it is not preceded by a negation (unless the negation itself creates a hedge) or if it appears in a specific syntactic frame (e.g., "I [hedge] that").
* **Action:** This requires updating the `tokenize_text` function to capture dependency relations or simple n-grams.

### Step 3: Re-Validation Loop
1. Update `src/extraction/hedge_extractor.py` with the refined lexicon.
2. Re-run `src/analysis/validation.py` against `data/processed/hedge_gold_standard.csv`.
3. Calculate the new precision score.

## 4. Decision Criteria

* **Success:** If Precision >= 0.80 after Step 1 or Step 2, document the final lexicon in `data/results/final_lexicon.yaml` and mark T001e as complete.
* **Failure:** If Precision remains < 0.80 after two rounds of refinement:
 * **Decision:** Halt the automated lexicon approach for this project.
 * **Fallback:** Proceed to manual hedge annotation for the full analysis set (T001k) or switch to a pre-trained model for hedge detection (e.g., a BERT-based classifier fine-tuned on hedge data), acknowledging this as a methodological deviation from the original "simple lexicon" spec.

## 5. Implementation Notes
* All changes to the lexicon must be version-controlled.
* The final lexicon must be stored in a configuration file (`data/config/hedge_lexicon.yaml`) rather than hardcoded in Python to ensure reproducibility.
* The `data/results/lexicon_validation_results.yaml` must be updated with the new precision metric before the project proceeds to Phase 2 (Feature Extraction).

## 6. Conclusion
The integrity of the study relies on the validity of the linguistic features. We will not proceed with the regression analysis (T021) until the feature extraction (hedge count) has a verified precision of >= 0.80. This plan ensures that we either fix the lexicon or transparently document the limitation and switch to a more robust annotation method.