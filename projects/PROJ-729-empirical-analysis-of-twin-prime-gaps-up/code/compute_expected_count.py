"""
Compute the expected twin prime count up to 10^9 using the Hardy-Littlewood constant
and compare it against the actual count from the generated dataset.

This script implements the verification for Task T013b:
- Calculates the theoretical expectation using the Hardy-Littlewood constant C2.
- Reads the actual count from data/raw/twin_primes.csv.
- Logs the deviation percentage.
"""
import sys
import math
import csv
from pathlib import Path

# Import configuration utilities from the project
from config import get_config

# Hardy-Littlewood Twin Prime Constant (C2)
# C2 = product over primes p >= 3 of (1 - 1/(p-1)^2)
# Value approx: 0.660161815846869573927812110014...
HARDY_LITTLEWOOD_CONSTANT = 0.660161815846869573927812110014

def get_theoretical_count(limit: float) -> float:
    """
    Compute the expected number of twin primes up to `limit` using the
    Hardy-Littlewood asymptotic formula:

    pi_2(x) ~ 2 * C2 * integral(2 to x) dt / (ln t)^2
    
    A simpler approximation often used for comparison is:
    pi_2(x) ~ 2 * C2 * x / (ln x)^2

    We use the integral approximation for better accuracy at 10^9,
    but for 10^9, the simpler form is often sufficient for a deviation check.
    However, the integral form is more rigorous.
    
    Integral of 1/(ln t)^2 dt is li_2(x) ~ x/(ln x)^2 + 2x/(ln x)^3 + ...
    
    Let's use the standard approximation: 2 * C2 * x / (ln x)^2
    This is the standard form for "expected count" in many computational contexts.
    """
    if limit <= 2:
        return 0.0
    
    log_x = math.log(limit)
    # Approximation: 2 * C2 * x / (ln x)^2
    expected = 2.0 * HARDY_LITTLEWOOD_CONSTANT * limit / (log_x * log_x)
    return expected

def get_actual_count(csv_path: Path) -> int:
    """
    Count the number of rows in the generated CSV file.
    Assumes the CSV has a header and at least one column 'p'.
    """
    count = 0
    try:
        with open(csv_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for _ in reader:
                count += 1
    except FileNotFoundError:
        raise FileNotFoundError(f"Required data file not found: {csv_path}")
    except Exception as e:
        raise RuntimeError(f"Error reading {csv_path}: {e}")
    
    return count

def main():
    config = get_config()
    data_dir = config.get('paths', {}).get('raw_data', 'data/raw')
    input_file = Path(data_dir) / "twin_primes.csv"
    
    # Limit for theoretical calculation (10^9)
    limit = 1_000_000_000.0

    print(f"--- T013b: Hardy-Littlewood Expected Count Verification ---")
    print(f"Limit (x): {limit:,.0f}")
    
    # 1. Compute Theoretical Expectation
    expected_count = get_theoretical_count(limit)
    print(f"Hardy-Littlewood Constant (C2): {HARDY_LITTLEWOOD_CONSTANT:.15f}")
    print(f"Theoretical Expected Count (pi_2(x) ~ 2*C2*x/(ln x)^2): {expected_count:,.2f}")
    
    # 2. Read Actual Count
    if not input_file.exists():
        print(f"ERROR: Data file {input_file} does not exist.")
        print("Please run code/generate_primes.py first to generate data/raw/twin_primes.csv")
        sys.exit(1)
    
    try:
        actual_count = get_actual_count(input_file)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except RuntimeError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    print(f"Actual Count from {input_file.name}: {actual_count:,}")
    
    # 3. Calculate Deviation
    if expected_count == 0:
        deviation_pct = 0.0
    else:
        deviation_pct = ((actual_count - expected_count) / expected_count) * 100.0
    
    print(f"Deviation Percentage: {deviation_pct:.4f}%")
    
    # Verification check (within ±5% as per task description T012/T013b context)
    if abs(deviation_pct) <= 5.0:
        print(f"VERIFICATION PASSED: Deviation ({deviation_pct:.4f}%) is within ±5% tolerance.")
    else:
        print(f"VERIFICATION WARNING: Deviation ({deviation_pct:.4f}%) exceeds ±5% tolerance.")
        
    print("--- End of Verification ---")

if __name__ == "__main__":
    main()
