"""
Script to validate AR(1) injection logic against target rho values.
This script generates real data, injects dependency, and verifies the autocorrelation.
"""
import numpy as np
import sys
import os

# Add code directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dependency_injector import ar1_inject, validate_ar1_injection

def main():
    print("Starting AR(1) Injection Validation...")
    
    # Parameters
    n_samples = 10000
    n_features = 1
    test_rhos = [0.0, 0.1, 0.3, 0.5, 0.7, 0.9]
    tolerance = 0.05 # 5% tolerance
    
    # Base data: White noise with very low variance to make the AR structure dominant
    # This ensures the estimated autocorrelation is driven by the injected process
    base_variance = 0.001
    base_data = np.random.normal(0, np.sqrt(base_variance), (n_samples, n_features))
    
    all_passed = True
    
    print(f"{'Target Rho':<12} {'Actual Rho':<12} {'Diff':<10} {'Status':<10}")
    print("-" * 44)
    
    for target_rho in test_rhos:
        # Inject dependency
        injected_data = ar1_inject(base_data, rho=target_rho, seed=42)
        
        # Validate
        is_valid, actual_rho = validate_ar1_injection(
            base_data, injected_data, target_rho, tolerance=tolerance
        )
        
        diff = abs(actual_rho - target_rho)
        status = "PASS" if is_valid else "FAIL"
        
        if not is_valid:
            all_passed = False
        
        print(f"{target_rho:<12.2f} {actual_rho:<12.4f} {diff:<10.4f} {status:<10}")
    
    print("-" * 44)
    if all_passed:
        print("Validation SUCCESS: All injected AR(1) processes match target within tolerance.")
        return 0
    else:
        print("Validation FAILED: Some injected AR(1) processes deviate beyond tolerance.")
        return 1

if __name__ == "__main__":
    sys.exit(main())