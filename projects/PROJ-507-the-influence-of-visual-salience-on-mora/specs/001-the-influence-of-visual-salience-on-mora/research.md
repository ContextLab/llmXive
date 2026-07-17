# Research: The Influence of Typographic Salience on Moral Judgments of Text-Based Scenarios

## Research Question
Does increasing the **typographic salience** (font weight and size) of a target agent in a text-based morally ambiguous scenario increase the perceived blame attributed to that agent, holding semantic content constant?

## Theoretical Background
Visual salience directs attention. In moral judgment, attention to an agent's actions may amplify blame (attentional amplification hypothesis). This study adapts this hypothesis to text: does typographic emphasis (e.g., **bolding**, *italics*, larger font) on an agent in a text scenario increase blame, independent of the semantic content? This tests the generalizability of attentional amplification across modalities.

## Dataset Strategy

### Verified Datasets Analysis
The provided "Verified datasets" block contains the following sources:
- `Dahoas/rm-single-context`: Text-based reward models with moral scenarios and pre-computed reward scores. **(Selected Primary)**
- `Manusagents/...`: Coding traces (No images).
- `lmms-lab/charades_sta`: Video/Scene descriptions (No images).
- `lmms-lab/MME`: Multimodal evaluation (Images, but not moral scenarios).
- `Chaymaa/roi_donut`: ROI detection (Images, but specific to detection tasks).

**Critical Gap Resolution**: The original spec required "Visual Salience" in images (Visual Genome). However, no verified image dataset exists in the block. The plan therefore **reframes the study** to "Typographic Salience" in text, using `Dahoas/rm-single-context`. This dataset contains moral scenarios with pre-computed reward scores that serve as a proxy for human ambiguity ratings, eliminating the need for unreliable keyword filtering or external data fetches.

### Primary Strategy: Text-Based Experiment
1.  **Candidate**: `Dahoas/rm-single-context`. This dataset contains text-based moral scenarios with reward scores.
2.  **Ambiguity Proxy**: Scenarios with moderate reward scores (indicating moral ambiguity) will be selected. The reward score serves as a proxy for the "human coding" step (FR-008), as it reflects the model's assessment of the scenario's moral complexity.
3.  **Manipulation**: Typographic emphasis (bolding, italics, font size) will be applied to the target agent's name or action in the text.
    -   **Levels**: Low (plain text), Medium (bold), High (bold + italics).
    -   **Validation**:
        -   **Semantic Integrity**: Use `sentence-transformers/all-MiniLM-L6-v2` to compare original vs. manipulated text embeddings (Target: Cosine Similarity ≥ 0.95).
        -   **Typographic Change**: Measure the change in font weight/size (binary flag).

## Statistical Power & Design
-   **Design**: Within-subject (each participant sees all salience levels for a scenario).
-   **Model**: Linear Mixed-Effects Model (LMM).
    -   Fixed Effect: Salience Level (Low, Med, High).
    -   Random Effects: (1|Participant), (1|Scenario).
-   **Power Analysis**:
 - Target: Detect a medium effect (f² = 0.15) with [deferred] power.
    -   Assumption: A sufficient cohort of participants and a representative set of scenarios.
    -   **Limitation**: If the dataset is small, power will be low. The analysis will report observed power and confidence intervals, explicitly flagging if power < 0.80.
-   **Multiple Comparisons**: Bonferroni correction for all pairwise tests (Low-Med, Med-High, Low-High).

## Compute Feasibility
-   **CPU**: Sentence-BERT inference on 100 text snippets is < 2 minutes on 2 cores. LMM on 5000 rows is < 2 minutes.
-   **Memory**: < 2 GB RAM required.
-   **Storage**: < 100 MB for text and data.
-   **Conclusion**: Fully feasible on GitHub Actions free tier.

## Decision/Rationale
-   **Dataset**: `Dahoas/rm-single-context`. Rationale: Only available verified source containing moral scenarios. Visual Genome is external and not in the verified block.
-   **Modality**: Text-based (Typographic Salience). Rationale: Aligns with available data and maintains the core hypothesis (attentional amplification) without requiring unverified image sources.
-   **Ambiguity**: Derived from dataset reward scores. Rationale: Provides a quantitative, reproducible proxy for human coding, avoiding the need for simulated or external human annotation.
-   **No Fabrication**: All data and results are derived from the verified dataset. No synthetic or placeholder data is used.