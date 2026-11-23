# Meta-Analysis Summary

## Panel Selection

- Method: intersection_empty (fallback to union)
- Panel Size: 50
- Selected Genes: [Top 50 genes from union of significant genes across LOO iterations]

## Fallback Information

- fallback_reason: intersection_empty
- panel_size: 50
- selected_genes: [GENE_A, GENE_B, GENE_C,...]

## Notes

- Intersection of significant genes across all tumor types was empty.
- Fallback to union of top-ranked genes (≤50) was executed as per FR-006.
- Genes ranked by aggregate p-value across all LOO iterations.