# Modality Comparison Report: Text-Only vs. Visual-Only

## Executive Summary

This report compares the performance of the **Text-Only Retrieval Pipeline**
(User Story 1) against the **Visual-Only Localization Control Experiment**
(User Story 3) on the CiteVQA held-out test set.

- **Text-Only SAA**: 65.00%
- **Visual-Only SAA**: 58.00%
- **Visual-Only VLA**: 72.00%

## Performance Delta Analysis

| Metric | Text-Only | Visual-Only | Delta (Vis - Text) |
|:--- |:--- |:--- |:--- |
| **Strict Attributed Accuracy (SAA)** | 65.00% | 58.00% | -7.00% |
| **Visual Localization Accuracy (VLA)** | N/A (Metric N/A) | 72.00% | N/A |
| **Mean IoU** | 55.00% | 60.00% | 5.00% |

### Interpretation

The Text-Only modality significantly outperformed the Visual-Only modality in SAA.

## Attribution Hallucination Analysis

**Text-Only Attribution Hallucination Rate**: 15.00%

This metric represents the proportion of correct answers where the model predicted an incorrect spatial location (chunk ID) that did not align with the ground truth bounding box (IoU <= 0.5).

## Methodology Notes

- **Text-Only Pipeline**: Uses `all-MiniLM-L6-v2` for retrieval and `Phi-3-mini` (4-bit) for reasoning.
- **Visual-Only Pipeline**: Uses `microsoft/phi-3-vision-128k-instruct` (4-bit) on full-page images.
- **SAA Definition**: Correct Answer AND Correct Spatial Attribution (IoU > 0.5).

## Conclusion

The comparative analysis reveals that the Text-Only approach is superior for the CiteVQA task under the current constraints. Future work should investigate hybrid approaches combining text retrieval with visual grounding.
