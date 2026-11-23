# PDF Report Layout Specification
**Project**: PROJ-331-investigating-the-influence-of-network-m
**Task**: T035a - Design PDF report layout
**Dependencies**: Spec FR-007, FR-009
**Library**: reportlab (v4.0+ recommended)

## 1. Document Structure

The final report (`results/report.pdf`) will be a single multi-page document with the following structure:

| Page | Section | Content |
|:--- |:--- |:--- |
| 1 | **Title Page** | Title, Authors, Date, Disclaimer, Abstract |
| 2 | **Methods Overview** | Pipeline summary, Data sources, Statistical methods |
| 3 | **Quality Control** | VIF results, Method selection (Pearson/Spearman), Power analysis |
| 4-N | **Motif Analysis** | One page per significant motif (scatter plot, stats) |
| N+1 | **Summary Table** | All correlations, p-values, significance flags |
| N+2 | **References** | Citations (Schaefer et al., etc.) |

## 2. Page Layout & Dimensions

- **Page Size**: A4 (210mm x 297mm)
- **Margins**:
 - Top: 25mm
 - Bottom: 25mm
 - Left: 20mm
 - Right: 20mm
- **Font**:
 - Headers: Helvetica-Bold, 14pt
 - Body: Helvetica, 11pt
 - Captions: Helvetica-Oblique, 9pt
 - Disclaimer: Helvetica, 8pt (Bottom of every page)

## 3. Data Mapping

The report generation script (`code/report.py`) will read the following JSON files and map them to PDF elements:

### A. `results/correlation_results.json`
*Source for Motif Pages and Summary Table*

| JSON Key | PDF Element | Description |
|:--- |:--- |:--- |
| `motif_id` | Header (Page N) | e.g., "Motif 23 (Feedforward Loop)" |
| `r_value` | Text Block | Pearson/Spearman correlation coefficient |
| `p_value_raw` | Text Block | Uncorrected p-value |
| `p_value_corrected` | Text Block | Bonferroni-corrected p-value |
| `is_significant` | Text Block | "Significant (p < 0.05)" or "Not Significant" |
| `n_subjects` | Text Block | Sample size used |

### B. `results/permutation_results.json`
*Source for Motif Pages (if significant)*

| JSON Key | PDF Element | Description |
|:--- |:--- |:--- |
| `motif_id` | Plot Caption | Matches correlation page |
| `empirical_p_value` | Text Block | Permutation test p-value |
| `null_distribution_mean` | Plot Annotation | Center of null distribution |
| `observed_statistic` | Plot Line | Vertical line on histogram |

### C. `results/power_analysis.json`
*Source for Quality Control Page*

| JSON Key | PDF Element | Description |
|:--- |:--- |:--- |
| `min_detectable_r` | Text Block | Minimum effect size detectable at 80% power |
| `adjusted_alpha` | Text Block | Bonferroni-adjusted alpha level |
| `statsmodels_version` | Footer/Note | Version used for calculation |

### D. `data/processed/quality_flags.json`
*Source for Quality Control Page*

| JSON Key | PDF Element | Description |
|:--- |:--- |:--- |
| `method_switched` | Text Block | "Method switched to Spearman due to VIF > 5" (if true) |
| `vif_value` | Text Block | Calculated VIF for network density |
| `zero_variance` | Warning Box | "Warning: Zero variance detected" (if true) |

## 4. Visual Elements (Plot Generation)

For each significant motif (Page N), the following plot is generated using `matplotlib` and embedded:

- **Type**: Scatter Plot
- **X-Axis**: Motif Z-Score (from `motif_z_aggregated.json`)
- **Y-Axis**: Resting-State Functional Connectivity Strength (from `rsfc.npy` aggregated per subject)
- **Annotations**:
 - Regression line (linear fit)
 - Text box with $r$ and $p$ values
 - Shaded region for 95% Confidence Interval
- **Export**: Saved to `figures/` as high-res PNG (300 DPI) before embedding in PDF.

## 5. Mandatory Disclaimer

**Location**: Fixed footer on every page, centered, 8pt font.
**Text**:
> "These findings are associational only and do not imply causation."

## 6. Implementation Flow (code/report.py)

1. **Load Data**: Read all three JSON inputs + quality flags.
2. **Initialize PDF**: `reportlab.pdfgen.canvas.Canvas`, set A4 size.
3. **Draw Title Page**: Static text + dynamic date.
4. **Draw Methods/Quality**: Iterate `quality_flags.json` and `power_analysis.json`.
5. **Loop Significant Motifs**:
 - Filter `correlation_results` where `is_significant == True`.
 - For each:
 - Generate Matplotlib scatter plot.
 - Save to `figures/`.
 - `canvas.drawImage()`.
 - Draw text stats.
6. **Draw Summary Table**: Iterate all motifs, draw table rows.
7. **Footer Loop**: Ensure disclaimer is drawn on every page.
8. **Save**: `canvas.save()` to `results/report.pdf`.

## 7. Error Handling

- If `correlation_results.json` is missing or empty, generate a "No Results Found" PDF with a warning.
- If plot generation fails, log error to `pipeline.log` and insert a placeholder box with "Plot generation failed" text.
- If disk space is insufficient for figures, raise `PipelineError`.

## 8. Dependencies

- `reportlab` (PDF generation)
- `matplotlib` (Plot generation)
- `pandas` (Data manipulation)
- `numpy` (Numerical operations)
- `json` (Data loading)
- `os` / `pathlib` (Path handling)

This layout design satisfies Spec FR-007 (Report Generation) and FR-009 (Mandatory Disclaimer).
