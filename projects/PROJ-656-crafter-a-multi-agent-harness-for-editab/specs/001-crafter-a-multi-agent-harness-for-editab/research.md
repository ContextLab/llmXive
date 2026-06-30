# Research: Crafter Multi-Agent Harness Validation

## Problem Statement

The project aims to validate the `Crafter` multi-agent harness, which claims to generate editable scientific figures from text descriptions. The core challenge is to verify that the pipeline functions end-to-end on a constrained CPU-only environment without relying on external paid APIs, while ensuring the generated outputs meet the structural requirements for editability (SVG). The research distinguishes between **Pipeline Integrity** (does the code run?) and **Functional Validity** (does the code produce valid, editable figures?).

## Dataset Strategy

The project relies on the `craftbench` dataset provided within the vendored `Crafter` repository. This dataset serves as the ground truth for evaluation.

| Dataset | Source URL | Usage | Notes |
| :--- | :--- | :--- | :--- |
| **CraftBench** | `external/Crafter/craftbench` (Vendored) | Evaluation Manifest | Contains input prompts, ground truth images, and metadata. No external download required. |
| **Sample Input** | `examples/sample_paper.txt` (Vendored) | Inference Test | A minimal text excerpt for the `inference.py` entry point. |

*Note: The project strictly relies on the vendored `craftbench` manifest to ensure reproducibility and avoid transient network failures.*

## Technical Approach

### 1. Inference Pipeline (`inference.py`)
The `inference.py` script orchestrates the multi-agent workflow:
1.  **Input Parsing**: Reads the text prompt and extracts `FigureSpec`.
2.  **Agent Coordination**:
    *   *Planner*: Decomposes the prompt into drawing steps.
    *   *Drawer*: Generates the raster image (using a local CPU model or mock).
    *   *Critic*: Validates the image against the prompt.
3.  **Output**: Saves the raster image to `output/` OR a placeholder if in "Dry-Run" mode.

**Constraint Handling**:
-   **Dry-Run Mode**: If `CRAFTER_MODE=mock`, the "Drawer" agent returns a pre-defined placeholder image (e.g., a 100x100 red square) to simulate output. This validates the *orchestration* but not the *generation*.
-   **Fail Fast**: If `CRAFTER_MODE` is not set and API keys are missing, the script exits with a non-zero code and a descriptive error within 30 seconds (Principle II).

### 2. SVG Conversion (`convert.py`)
The `convert.py` script performs raster-to-vector conversion:
1.  **Input Validation**: Checks if the input image is a "placeholder" (e.g., specific file hash or size). If so, it logs a warning and **skips** vectorization to prevent invalid SVG generation.
2.  **Edge Detection**: Identifies shapes and text boundaries (only if input is real).
3.  **Vectorization**: Generates `<path>`, `<rect>`, and `<text>` elements.
4.  **Validation**: Ensures the output is valid XML and opens in standard editors.

### 3. Evaluation (`CraftBench`)
The `craftbench/evaluation.run_eval` module:
1.  **Iterates** over the `manifest.json`.
2.  **Compares** generated figures against ground truths.
3.  **Calculates** `success_rate`, `quality_score`, and `editability_score`.

**Metric Independence & Validation**:
-   The internal `craftbench` metrics are acknowledged as *internal* to the vendored code and are used for **Pipeline Integrity** (PI-001 to PI-003).
-   To avoid circularity and ensure **Scientific Soundness**, an **External Validation Step** is added for **Functional Validity** (FV-001 to FV-004):
    -   **Quality**: A pixel-diff against the ground truth image (if available) or a separate LLM judge prompt.
    -   **Editability**: **Structural Element Overlap (SEO)**. Instead of string similarity, the SVGs are parsed into a DOM tree. The metric counts the overlap of node types (e.g., `<text>`, `<path>`) and attributes between the generated SVG and the ground truth SVG. This is robust against formatting differences.

## Causal Validity & Construct Validity

-   **Construct Validity**: The "Dry-Run" mode validates the *harness logic* (orchestration), not the *multi-agent behavior*. The plan explicitly states that in CI, we are validating the *pipeline*, not the *agent intelligence*. Claims about "publication-quality figures" are reserved for "Full-Run" mode.
-   **Causal Validity**: In "Dry-Run" mode, no causal claims about the *quality* of the generated figure can be made. Success is defined as "Pipeline Completion" ([deferred]). In "Full-Run" mode, quality metrics are valid.
-   **Dataset Fit**: The `craftbench` dataset is assumed to contain all necessary inputs. If a required variable is missing, the plan will flag the gap rather than fabricate data.

## Risk Mitigation

-   **API Rate Limiting**: Implemented via exponential backoff (30s wait, 3 retries) as per Edge Cases.
-   **Memory Constraints**: Data is processed in chunks; large inputs trigger a graceful "Input too large" error.
-   **SVG Parsing**: `lxml` is used for strict XML parsing; malformed outputs are logged with line numbers.
-   **Placeholder Handling**: `convert.py` explicitly detects and skips placeholder inputs to prevent invalid SVG generation.

## Decision Rationale

**Why Mock Mode?**
The GitHub Actions free tier does not support persistent external API keys for paid services. To ensure the *reproducibility* of the pipeline logic (FR-001, FR-004), a "Dry-Run" mode is essential. This allows the validation of the *orchestration* and *conversion* logic without dependency on external service availability.

**Why CPU-Only?**
The `Crafter` backbone models (if present) are likely lightweight or replaceable with CPU-tractable alternatives for the purpose of *validation*. Training or running large models is out of scope for this feature; the focus is on the *harness* logic.

**Why Structural Element Overlap?**
String similarity is scientifically invalid for SVGs due to formatting differences. DOM-based comparison (SEO) is robust and accurately reflects structural editability.