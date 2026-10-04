# Decision Record 002: Native Ground Truth and Statistical Test Amendment

## Status
Accepted

## Context
The initial specification (Draft) proposed using upsampled low-resolution images as ground truth for high-resolution fidelity measurement (FR-004) and a one-sample t-test (SC-005) for statistical validation.

## Decision
1. **Ground Truth**: We will use **native 1024x1024 ground truth** images available in the ImageNet-1K and COCO datasets, rather than upscaling low-resolution inputs. This provides a scientifically accurate baseline for high-resolution reconstruction quality.
2. **Statistical Test**: We will replace the one-sample t-test with a **Paired t-test** (if normality assumptions hold) or **Wilcoxon signed-rank test** (if non-normal) to compare texture complexity against reconstruction error. This correctly models the paired nature of the data (same image, different complexity metrics).

## Consequences
- **Positive**: Increases scientific rigor; ensures fidelity metrics are not confounded by interpolation artifacts from upsampling.
- **Positive**: The statistical test now correctly addresses the hypothesis regarding the relationship between texture and error.
- **Alignment**: This decision amends **FR-004** and **SC-004** (replacing SC-005) in the specification.