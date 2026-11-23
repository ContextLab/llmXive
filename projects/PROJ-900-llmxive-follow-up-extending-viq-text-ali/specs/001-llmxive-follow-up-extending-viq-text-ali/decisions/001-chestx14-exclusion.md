# Decision Record 001: Exclusion of ChestX-ray14

## Status
Accepted

## Context
The initial project scope included ChestX-ray14 as a potential dataset for evaluating resolution invariance. However, ChestX-ray14 consists of medical X-ray images, which have fundamentally different texture, frequency, and semantic properties compared to natural images (COCO, ImageNet).

## Decision
We will explicitly exclude ChestX-ray14 from the training, validation, and testing phases of this study. The study will focus exclusively on natural images to ensure that the "resolution invariance" hypothesis is tested within a consistent domain.

## Consequences
- **Positive**: Eliminates domain shift confounds; ensures that any observed fidelity drop is due to resolution, not domain mismatch.
- **Negative**: Reduces the total volume of available data, requiring careful management of the COCO/ImageNet sampling strategy.
- **Alignment**: This decision is reflected in **FR-003** and **US-2** in the updated specification.