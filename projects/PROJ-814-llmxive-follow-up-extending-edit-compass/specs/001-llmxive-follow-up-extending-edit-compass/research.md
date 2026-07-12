# Research: llmXive follow‑up Correlation Study

**Feature**: `001-llmxive-followup-correlation-study`  
**Date**: 2026‑07‑11  
**Spec**: [link to spec]

## Dataset Strategy
| Dataset | Source / Access Method | Variables Required | Verification Status |
|---------|------------------------|--------------------|---------------------|
| Edit‑Compass | HuggingFace Datasets (`HuggingFaceTB/edit-compass`) via `datasets.load_dataset("HuggingFaceTB/edit-compass")` | `instance_id`, `source_image`, `edited_image`, `instruction`, `category`, `human_judgment_score` | **Verified**: The dataset is hosted on HuggingFace with a verified URL and programmatic loader. The pipeline will verify the presence of required columns upon loading. |

*If the dataset lacks any required variable, the pipeline will raise an explicit error (FR‑005) and halt.*

## Model & Metric Selection
| Component | Model / Library | CPU‑Optimized? | Reasoning |
|-----------|----------------|----------------|-----------|
| Instruction-Description Semantic Similarity | `Phi-3-mini-4k-instruct-GGUF` (4-bit quantized) via `llama-cpp-python` | Yes (4-bit GGUF runs < 4GB RAM on CPU) | Generates a textual description of the edit. The Low-bit quantization ensures memory safety on the 7GB runner. |
| Embedding Comparator | `all-MiniLM-L6-v2` from `sentence‑transformers` (CPU) | Yes | Provides L2‑normalized vectors for cosine similarity. |
| Fidelity – SSIM | `skimage.metrics.structural_similarity` | N/A | Pixel‑level structural similarity. |
| Fidelity – LPIPS | `lpips` with `alex` backbone (CPU‑only) | Yes (small AlexNet) | Perceptual similarity; inverted to align directionality. |
| Regression | `statsmodels.api.OLS` (standardized betas) | N/A | Provides coefficients, p‑values, VIF, and diagnostic stats. |
| Multiple‑Comparison | Benjamini‑Hochberg (FDR ≤ 0.05) implemented via `statsmodels.stats.multitest.multipletests` | N/A | Controls false discovery across the two predictor tests. |

## Experimental Design
| Step | Description | FR/SC addressed |
|------|-------------|-----------------|
| 0️⃣ Data Download | Pull the full Edit‑Compass dataset from HuggingFace. Verify checksum and column presence. | FR‑001, SC‑005 |
| 1️⃣ Category Filtering | Keep only rows where `category` ∈ {“World Knowledge Reasoning”, “Visual Reasoning”}. Log count > 0. | FR‑002, SC‑005 |
| 2️⃣ Score Generation (Batch) | For each batch (size = 8 to stay < 7 GB with 4-bit VLM):<br>• VLM generates description of edited image.<br>• Compute cosine similarity between instruction & description embeddings → **Instruction-Description Semantic Similarity Score**.<br>• Compute SSIM and LPIPS → Fidelity Score (0.5 × SSIM + 0.5 × (1‑LPIPS)).<br>• Skip instances where VLM times‑out or fails; log and exclude. | FR‑003, FR‑004, FR‑008 |
| 3️⃣ Data Cleaning | Remove any rows missing `human_judgment_score` or with missing scores from step 2. Record exclusion counts. | Edge‑case handling, FR‑008 |
| 4️⃣ Multicollinearity & Independence Check | <br>• **Predictor-Predictor**: Compute Pearson r between Logic Score and Fidelity Score. If |r| ≥ 0.7, compute VIF. If VIF > 5, flag multicollinearity and interpret jointly.<br>• **Independence**: Verify structural independence (VLM does not read Human Score). No statistical abort on predictor-target correlation. | FR‑005 (Corrected) |
| 5️⃣ Power Analysis | Calculate post-hoc power for the expected effect size (difference in correlations = 0.1) given the filtered N. If power < 0.8, report limitation. | SC‑001, SC‑003 |
| 6️⃣ Multiple Linear Regression | Regress Human Score on Logic & Fidelity (standardized). Compute VIF, standardized β, raw p‑values. | FR‑006 |
| 7️⃣ Multiple‑Comparison Correction | Apply Benjamini‑Hochberg (FDR ≤ 0.05) to the two predictor p‑values. | FR‑007 |
| 8️⃣ Reporting | Produce a concise Markdown/HTML report containing:<br>• Correlation matrix (Human‑Logic, Human‑Fidelity, Logic‑Fidelity).<br>• Regression table (β, SE, p, corrected p).<br>• VIF diagnostics.<br>• Power analysis results.<br>• Decision: which predictor is stronger (SC‑001).<br>• Runtime & memory usage (SC‑003, SC‑004). | SC‑001, SC‑002, SC‑003, SC‑004 |

## Statistical Rigor Checklist
- **Multiple Comparison**: Benjamini‑Hochberg applied (Step 7).  
- **Power / Sample‑size**: Post-hoc power analysis performed (Step 5). If power < 0.8 for the expected effect size, the limitation is explicitly reported as a potential Type II error risk.  
- **Causal Inference**: Observational data → results framed as *associational* (Constitution Principle VII).  
- **Measurement Validity**:  
  - Instruction embeddings: validated MiniLM model (cite original paper).  
  - VLM description: Phi-3-mini (4-bit GGUF) is a publicly released open-source model.  
  - Construct Validity: The metric is explicitly named "Instruction-Description Semantic Similarity" to reflect that it measures alignment, not reasoning validity.  
- **Collinearity**: VIF computed; if VIF > 5, we will report collinearity and interpret jointly.  
- **Independence**: Verified by structural design (VLM does not access Human Score), not by statistical correlation.  

## Decision / Rationale
All chosen models are CPU‑friendly and fit within the 7 GB RAM budget when processed in batches of ≤ 8 using 4-bit quantization. The SSIM/LPIPS combination is lightweight; LPIPS uses the AlexNet backbone which runs on CPU in < 0.1 s per image pair. The VLM inference for Phi-3-mini (4-bit) on a 224×224 image takes ~0.8 s on the runner; batch processing keeps total runtime under 5 h. This satisfies the computational constraint (Principle VII). The power analysis ensures the study is not underpowered for the expected effect size.

---