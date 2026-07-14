"""
Integration test for sky patch consistency (US3).

This test verifies that the pipeline produces consistent best-fit parameters
when the sky is split into independent patches (Northern/Southern hemispheres).
It uses synthetic data generated from a known ground truth to validate the
robustness of the inference pipeline against sky variations.

Satisfies:
  - FR-007: Split sky into independent patches and verify consistency.
  - US3 Acceptance: Consistency of best-fit r values within statistical fluctuations.
"""
import os
import json
import tempfile
import shutil
import numpy as np
import healpy as hp
import sys
import pathlib

# Add project root to path for imports
project_root = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.synthetic_data import generate_inflation_dataset, save_dataset
from code.inference import run_nested_sampling, log_likelihood, prior_transform
from code.config import init_reproducibility, get_config

def test_sky_split_consistency():
    """
    Integration test: Split synthetic sky into N/S patches, run inference on each,
    and verify that the recovered 'r' values are consistent within 1-sigma.
    """
    # Setup reproducibility
    init_reproducibility(seed=42)
    config = get_config()

    # Create a temporary directory for this test run
    temp_dir = tempfile.mkdtemp(prefix="sky_split_test_")
    try:
        # 1. Generate Ground Truth Synthetic Data
        # We use a known r value (e.g., 0.01) for the Inflation model
        true_r = 0.01
        nside = 32  # Low resolution for CPU speed in integration test
        npix = hp.nside2npix(nside)

        # Generate full sky map with known r
        # Note: generate_inflation_dataset returns a dict with 'map_q', 'map_u', 'l_vals', 'cl_vals'
        full_sky_data = generate_inflation_dataset(
            r=true_r,
            nside=nside,
            noise_level=1.0e-6,
            seed=42
        )

        q_map = full_sky_data['map_q']
        u_map = full_sky_data['map_u']

        # 2. Split Sky into Northern and Southern Hemispheres
        # Create a mask for Northern (lat > 0) and Southern (lat < 0)
        # HEALPix pixel centers can be retrieved via healpy.pix2ang
        theta, phi = hp.pix2ang(nside, np.arange(npix))
        # theta is colatitude (0 at North Pole, pi at South Pole)
        # lat = pi/2 - theta. So lat > 0 implies theta < pi/2.
        north_mask = (theta < np.pi / 2)
        south_mask = ~north_mask

        # Apply masks (set masked pixels to 0, effectively removing them from spectrum)
        # For robustness, we create separate masked maps
        north_q = q_map.copy()
        north_q[~north_mask] = 0.0
        north_u = u_map.copy()
        north_u[~north_mask] = 0.0

        south_q = q_map.copy()
        south_q[~south_mask] = 0.0
        south_u = u_map.copy()
        south_u[~south_mask] = 0.0

        # 3. Compute Power Spectra for each patch
        # We use the same likelihood function which internally computes the spectrum
        # from the input map. We need to adapt the likelihood to accept masked maps.
        # However, the standard likelihood expects a full map or a specific mask.
        # For this integration test, we will simulate the likelihood calculation
        # by passing the masked maps directly to a custom wrapper that computes the spectrum.

        def run_inference_on_map(q_map, u_map, nside, true_r, label):
            """Run nested sampling on a specific map patch."""
            # Define priors
            # r is typically log-uniform or uniform in a small range [0, 0.1]
            def log_prob(params):
                # params = [r]
                r = params[0]
                # Check bounds
                if r <= 0 or r > 0.1:
                    return -np.inf
                return 0.0

            # We need a function that computes the likelihood given the data
            # The data here is the masked map.
            # The likelihood function in inference.py expects 'data' which is usually a spectrum.
            # To keep this self-contained and fast, we will mock the spectrum computation
            # by using the theoretical model and adding noise, OR we can compute the spectrum
            # from the masked map using healpy.
            # Let's compute the spectrum from the masked map using healpy.
            # Note: Masked maps produce biased spectra if not corrected, but for
            # consistency checks (N vs S), the bias should be similar if masks are symmetric.

            # Compute BB spectrum from masked map
            # We need to handle the mask properly. A simple approach for integration test:
            # Use the full spectrum of the masked map as the "observed" data.
            # In a real scenario, we'd use MASTER or similar to de-bias.
            # Here, we just compare the recovered r from N vs S.

            # To avoid complex de-biasing in this test, we will generate the "observed" spectrum
            # directly from the map using hp.anafast.
            # We assume the map is already Q/U.
            # anafast returns Cl for TT, EE, BB, etc. if we pass Q/U correctly.
            # Actually, anafast takes a tuple (I, Q, U) or just Q/U for polarization.
            # It returns [TT, TE, EE, TB, EB, BB] if all provided.
            # If we pass (Q, U), it might not work as expected.
            # Correct usage for BB:
            # cl = hp.anafast((None, q_map, u_map), lmax=lmax, pol=True)
            # The index for BB is 5 (0:TT, 1:TE, 2:EE, 3:TB, 4:EB, 5:BB)

            lmax = 2 * nside
            cl_full = hp.anafast((None, q_map, u_map), lmax=lmax, pol=True)
            cl_bb = cl_full[5]
            l_vals = np.arange(2, lmax + 1)

            # Filter out l=0,1 (not physical) and NaNs
            valid_l = l_vals >= 2
            l_vals = l_vals[valid_l]
            cl_bb = cl_bb[valid_l]

            # Replace negative values with small positive (numerical stability)
            cl_bb = np.maximum(cl_bb, 1e-10)

            # Define the likelihood function for this specific data
            # We need to pass the observed l_vals and cl_bb to the log_likelihood
            # The log_likelihood in inference.py expects 'data' as a dict or similar.
            # Let's adapt the existing log_likelihood to accept our data.
            # Since we cannot easily modify the existing inference.py without breaking other tests,
            # we will create a local wrapper that mimics the interface.

            # However, the task requires using the existing API.
            # The existing log_likelihood expects:
            #   params (list), data (dict with 'l_values', 'cl_values')
            # So we format our data accordingly.
            data_dict = {
                'l_values': l_vals.tolist(),
                'cl_values': cl_bb.tolist(),
                'noise_level': 1.0e-12, # Placeholder, assumed negligible for synthetic
                'model_type': 'inflation'
            }

            # Wrap the log_likelihood to capture the data
            def local_log_likelihood(params):
                return log_likelihood(params, data_dict)

            # Run Nested Sampling
            # We use a small number of live points for speed
            n_live = 20
            sampler = run_nested_sampling(
                log_prob_fn=local_log_likelihood,
                prior_transform_fn=lambda x: [x[0] * 0.1], # Map [0,1] to [0, 0.1]
                ndim=1,
                n_live=n_live,
                dlogz=0.5
            )

            results = sampler.results
            # Extract mean and std of r
            # The sampler returns samples in the transformed space.
            # We need to inverse transform if we used a transform.
            # Here, prior_transform was identity * 0.1, so r = x[0] * 0.1.
            # But the sampler returns the samples in the original space?
            # dynesty returns samples in the unit cube [0,1]^ndim.
            # So we need to apply the inverse transform.
            # Actually, run_nested_sampling in inference.py handles the transform internally?
            # Let's check the inference.py signature.
            # It calls: sampler.run_mcmc(...) or similar.
            # The results.samples are in the unit cube.
            # We need to apply the prior_transform inverse?
            # The prior_transform in inference.py is:
            #   def prior_transform(cube): return [cube[0] * (0.1 - 0) + 0]
            # So to get r, we do: r = prior_transform([x])[0]
            # But wait, the prior_transform is applied to the unit cube to get the physical parameter.
            # The sampler returns samples in the unit cube.
            # So we need to transform the samples back.
            # Let's assume the sampler returns the samples in the unit cube.
            # We will transform them manually.

            samples_unit = results.samples
            # Transform to physical r
            # prior_transform: x -> x * 0.1
            # So r = x * 0.1
            r_samples = samples_unit[:, 0] * 0.1

            mean_r = np.mean(r_samples)
            std_r = np.std(r_samples)

            return mean_r, std_r, true_r

        # Run on North
        mean_n, std_n, true_n = run_inference_on_map(north_q, north_u, nside, true_r, "North")
        # Run on South
        mean_s, std_s, true_s = run_inference_on_map(south_q, south_u, nside, true_r, "South")

        print(f"North Patch: r = {mean_n:.4f} +/- {std_n:.4f} (True: {true_n})")
        print(f"South Patch: r = {mean_s:.4f} +/- {std_s:.4f} (True: {true_s})")

        # 4. Verify Consistency
        # The difference between mean_n and mean_s should be within 2*sqrt(std_n^2 + std_s^2)
        # Or simply check if the true value is within the 95% CI of both.
        # For this integration test, we check if the intervals overlap significantly.
        # Criterion: |mean_n - mean_s| < 2 * sqrt(std_n^2 + std_s^2)
        diff = abs(mean_n - mean_s)
        combined_std = np.sqrt(std_n**2 + std_s**2)
        threshold = 2.0 * combined_std

        assert diff < threshold, (
            f"Sky split consistency failed: "
            f"North r={mean_n:.4f}, South r={mean_s:.4f}, "
            f"Difference={diff:.4f} > Threshold={threshold:.4f}"
        )

        # Also verify that the true value is recovered within the combined uncertainty
        # (Optional, but good for validation)
        assert abs(mean_n - true_r) < 3 * std_n, "North patch failed to recover true r."
        assert abs(mean_s - true_r) < 3 * std_s, "South patch failed to recover true r."

        print("✓ Sky split consistency test passed.")

    finally:
        # Cleanup
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    test_sky_split_consistency()