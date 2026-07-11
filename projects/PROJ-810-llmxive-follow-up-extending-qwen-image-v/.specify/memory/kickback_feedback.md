# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 1 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The plan proposes using 'Masked SSIM' to evaluate edited images (US-02) by comparing non-text regions. However, the vector arithmetic operation ($z_{new} = z_{doc} - \mu_{text old} + \mu_{text new}$) operates on the *entire* latent vector of the document. If the VAE latent space is not perfectly disentangled (which is the hypothesis being tested), the 'text' vector component likely contains spatial/layout information. Subtracting it may distort the non-text regions, causing the Masked SSIM to fail even if the text swap was successful. The methodology lacks a control for 'layout preservation' that is independent of the VAE's reconstruction fidelity, potentially conflating disentanglement failure with editing failure.
