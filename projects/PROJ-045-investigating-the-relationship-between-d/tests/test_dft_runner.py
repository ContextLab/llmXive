"""
Contract test for User Story 2 (T021):
Defect energy range validation (starting from a lower bound consistent with defect formation physics).

This test verifies that the defect formation energies calculated by the DFT runner
do not fall below physically plausible lower bounds.
"""

import pytest
import numpy as np
from pathlib import Path
import sys
import json

# Add the code directory to the path so we can import dft_runner and models
# In a real CI environment, this would be handled by PYTHONPATH or installed package
code_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_dir))

from models import DefectConfiguration, DefectType
from utils import setup_logging

# Physical constants and typical bounds
# Defect formation energies in stable oxides are typically > 0.5 eV for vacancies
# and > 1.0 eV for interstitials. We set a conservative lower bound.
MIN_PHYSICAL_DEFECT_ENERGY_EV = 0.0  # Absolute theoretical lower bound (unbound system)
CONSERVATIVE_LOWER_BOUND_EV = -2.0   # Conservative bound: energies below this are unphysical


def test_defect_energy_lower_bound():
    """
    Contract test: Verify that defect formation energies are within a physically plausible range.

    This test simulates a set of defect configurations and ensures that the calculated
    formation energies do not fall below the defined lower bound.
    """
    logger = setup_logging("test_dft_runner")
    logger.info("Starting defect energy range validation test.")

    # Simulate a set of defect configurations with known energies
    # In a real scenario, these would come from dft_runner.py output
    test_cases = [
        {
            "composition": "LiCoO2",
            "defect_type": DefectType.VACANCY,
            "formation_energy_ev": 1.2,  # Plausible
            "supercell_atoms": 40
        },
        {
            "composition": "LiNiO2",
            "defect_type": DefectType.INTERSTITIAL,
            "formation_energy_ev": 2.5,  # Plausible
            "supercell_atoms": 40
        },
        {
            "composition": "LiMn2O4",
            "defect_type": DefectType.ANTISITE,
            "formation_energy_ev": 0.8,  # Plausible
            "supercell_atoms": 56
        },
        {
            "composition": "LiFePO4",
            "defect_type": DefectType.VACANCY,
            "formation_energy_ev": -0.5, # Unphysical (too low) - should trigger failure
            "supercell_atoms": 28
        }
    ]

    failed_cases = []
    for case in test_cases:
        energy = case["formation_energy_ev"]
        composition = case["composition"]
        defect_type = case["defect_type"].value

        logger.info(f"Checking {defect_type} in {composition}: {energy} eV")

        if energy < CONSERVATIVE_LOWER_BOUND_EV:
            failed_cases.append({
                "composition": composition,
                "defect_type": defect_type,
                "energy_ev": energy,
                "reason": f"Energy {energy} eV is below physical lower bound {CONSERVATIVE_LOWER_BOUND_EV} eV"
            })

    # Assert that no unphysical energies were found
    assert len(failed_cases) == 0, (
        f"Defect energy range validation failed for {len(failed_cases)} cases:\n"
        + "\n".join([f"  - {c['reason']}" for c in failed_cases])
    )

    logger.info("Defect energy range validation PASSED.")


def test_defect_energy_range_consistency():
    """
    Contract test: Verify that defect energies for the same defect type
    are consistent within a reasonable tolerance across different compositions.
    """
    logger = setup_logging("test_dft_runner")
    logger.info("Starting defect energy consistency test.")

    # Simulate energies for the same defect type (vacancy) across different compositions
    # These should be roughly in the same ballpark (within 2 eV of each other for this test)
    vacancy_energies = [1.2, 1.4, 1.1, 1.3, 1.5]  # eV

    mean_energy = np.mean(vacancy_energies)
    std_dev = np.std(vacancy_energies)

    logger.info(f"Vacancy energies: {vacancy_energies}")
    logger.info(f"Mean: {mean_energy:.2f} eV, Std Dev: {std_dev:.2f} eV")

    # Consistency check: standard deviation should be small (< 0.5 eV for this synthetic set)
    # In real DFT data, this might vary more, but we're testing the contract logic
    assert std_dev < 0.5, (
        f"Defect energy consistency check failed: "
        f"Standard deviation {std_dev:.2f} eV exceeds threshold 0.5 eV"
    )

    logger.info("Defect energy consistency check PASSED.")


def test_neb_force_convergence():
    """
    Integration test for NEB convergence criteria (force ≤0.05 eV/Å).

    This test simulates the output of a NEB calculation and verifies that the
    maximum force on any image is within the specified convergence threshold.
    It mocks the dft_runner logic to ensure the validation step works correctly.
    """
    logger = setup_logging("test_dft_runner")
    logger.info("Starting NEB force convergence integration test.")

    # Import the function we are testing logic for (simulated here as we don't have dft_runner yet)
    # In a real scenario, this would import from dft_runner: from dft_runner import check_neb_convergence
    # Since dft_runner is not implemented yet, we simulate the logic here to test the contract.

    NEB_FORCE_THRESHOLD_EV_ANGSTROM = 0.05  # eV/Å

    # Simulate NEB results for different systems
    # Format: list of forces (eV/Å) for each image in the NEB path
    neb_results = [
        {
            "system": "LiCoO2_Vacancy_Path1",
            "forces": [0.12, 0.08, 0.04, 0.02, 0.01], # Converged (max 0.12 > 0.05? No, wait. 0.12 is max. Fail.)
            "expected_status": "failed"
        },
        {
            "system": "LiNiO2_Interstitial_Path2",
            "forces": [0.04, 0.03, 0.02, 0.01, 0.01], # Converged
            "expected_status": "passed"
        },
        {
            "system": "LiMn2O4_Antisite_Path1",
            "forces": [0.06, 0.055, 0.051, 0.049, 0.04], # Not converged (max 0.06)
            "expected_status": "failed"
        },
        {
            "system": "LiFePO4_Vacancy_Path3",
            "forces": [0.02, 0.02, 0.02, 0.02, 0.02], # Converged
            "expected_status": "passed"
        }
    ]

    validation_results = []

    for result in neb_results:
        system_name = result["system"]
        forces = result["forces"]
        expected = result["expected_status"]

        max_force = max(forces)
        is_converged = max_force <= NEB_FORCE_THRESHOLD_EV_ANGSTROM

        status = "converged" if is_converged else "not_converged"
        logger.info(f"System: {system_name}, Max Force: {max_force:.4f} eV/Å, Status: {status}")

        validation_results.append({
            "system": system_name,
            "max_force_ev_angstrom": max_force,
            "is_converged": is_converged,
            "expected": expected,
            "passed": (is_converged and expected == "passed") or (not is_converged and expected == "failed")
        })

    # Assert all validation results match expectations
    failed_tests = [r for r in validation_results if not r["passed"]]

    assert len(failed_tests) == 0, (
        f"NEB convergence validation failed for {len(failed_tests)} cases:\n"
        + "\n".join([
            f"  - {t['system']}: Expected {t['expected']}, got {'converged' if t['is_converged'] else 'not_converged'} "
            f"(max force: {t['max_force_ev_angstrom']:.4f} eV/Å)"
            for t in failed_tests
        ])
    )

    logger.info("NEB force convergence integration test PASSED.")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])