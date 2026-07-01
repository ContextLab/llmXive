# LiveEdit Proxy Evaluation

## Context
The original `LiveEdit` repository contains only the LaTeX manuscript. No source code (Python/PyTorch) was available to port.

## Adaptation Strategy
This script implements a **proxy evaluation** of the paper's core claims:
1.  **Three-Stage Distillation:** Simulated by comparing a "Student" (simple causal color shift) against a "Teacher" (stronger color shift). The metrics (PSNR/SSIM) measure the quality of the student approximation.
2.  **AR-oriented Mask Cache:** Implemented as a memory buffer that reuses masks from the previous frame with 90% probability, simulating the speedup claimed in the paper.
3.  **Real Data:** Uses a real, small video clip (`bouncingball.avi`) downloaded from a public OpenCV sample source. No synthetic/random data is used.

## Approximations
-   **Model:** The actual Diffusion Transformer is replaced by simple image processing operations (color shifting) to fit CPU constraints and lack of weights.
-   **Scale:** Only 20 frames are processed to ensure the run completes within the 25-minute CPU budget.
-   **FPS:** The reported FPS is "simulated" based on the lightweight operations; the real model's 12.66 FPS is the target, not the output of this proxy.

## Output
-   `data/metrics.json`: Quantitative results (PSNR, SSIM, Simulated FPS, Cache Hit Rate).
-   `figures/editing_comparison.png`: Visual comparison of Original, Student, and Teacher outputs.
