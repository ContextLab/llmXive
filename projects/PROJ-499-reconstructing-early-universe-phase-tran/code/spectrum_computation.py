import os
import json
import numpy as np
import healpy as hp
from typing import Dict, Any, Tuple, Optional
from config import get_config

def compute_bb_spectrum(map_file: str) -> np.ndarray:
    """Computes the BB power spectrum from a HEALPix map."""
    try:
        # Load the map using healpy
        m = hp.read_map(map_file, verbose=False)

        # Calculate the angular power spectrum
        lmax = 300  # Maximum multipole to compute
        cl_bb = hp.anafast(m, lmax=lmax)

        return cl_bb

    except Exception as e:
        print(f"Error computing BB spectrum: {e}")
        return np.array([])


def validate_sky_coverage(map_file: str) -> float:
  """Validates the sky coverage of a HEALPix map."""
  try:
      m = hp.read_map(map_file, verbose=False)
      mask = m != hp.UNMASK  # Create mask from non-masked pixels
      coverage = np.sum(mask) / hp.nside2npix(hp.get_nside(map_file))
      return coverage

  except Exception as e:
      print(f"Error validating sky coverage: {e}")
      return 0.0

def save_spectrum_results(cl_bb: np.ndarray, output_path: str):
    """Saves the BB power spectrum to a JSON file."""
    try:
        with open(output_path, 'w') as f:
            json.dump({"l": list(range(len(cl_bb))), "cl_bb": cl_bb.tolist()}, f)

    except Exception as e:
        print(f"Error saving spectrum results: {e}")


def main():
    """Main function to compute and save the BB power spectrum."""
    config = get_config()
    map_file = "data/derived/masked_bmode.fits" # Assuming masked map is available

    cl_bb = compute_bb_spectrum(map_file)

    if cl_bb.size > 0:
        save_spectrum_results(cl_bb, "data/derived/cl_bb_spectrum.json")
        print("BB spectrum computed and saved successfully.")
    else:
        print("Failed to compute BB spectrum.")


if __name__ == "__main__":
    main()
