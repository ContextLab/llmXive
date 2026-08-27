import os
import logging
import pandas as pd
from pathlib import Path
from utils import get_logger

def calculate_type2_error_delta(power_csv_path: str) -> pd.DataFrame:
    """
    Calculate Type II error delta (1 - power) relative to the 30m baseline.

    The 30m resolution serves as the baseline (assumed power = 1.0 or the
    measured maximum power at the highest resolution). The delta represents
    the loss in statistical power as resolution coarsens.

    Args:
        power_csv_path: Path to the CSV file containing power results.
                        Expected columns: 'resolution', 'power'.

    Returns:
        DataFrame with original columns plus 'type2_error_delta'.
    """
    logger = get_logger(__name__)
    logger.info(f"Loading power results from {power_csv_path}")

    if not os.path.exists(power_csv_path):
        raise FileNotFoundError(f"Power results file not found: {power_csv_path}")

    df = pd.read_csv(power_csv_path)

    if 'resolution' not in df.columns or 'power' not in df.columns:
        raise ValueError(
            f"CSV must contain 'resolution' and 'power' columns. "
            f"Found: {df.columns.tolist()}"
        )

    # Identify the baseline resolution (30m)
    # Assuming resolution is stored as string like "30m", "60m", etc.
    baseline_row = df[df['resolution'] == '30m']

    if baseline_row.empty:
        # If 30m is not explicitly in the file, assume the row with the
        # smallest resolution number (highest resolution) is the baseline.
        # Extract numeric part for sorting
        def get_res_num(res_str):
            try:
                return int(''.join(filter(str.isdigit, res_str)))
            except ValueError:
                return float('inf')

        df['res_num'] = df['resolution'].apply(get_res_num)
        baseline_row = df.loc[df['res_num'].idxmin()]
        baseline_power = baseline_row['power']
        logger.warning(f"30m not found. Using {baseline_row['resolution']} as baseline with power {baseline_power}")
    else:
        baseline_power = baseline_row['power'].iloc[0]
        logger.info(f"Baseline (30m) power: {baseline_power}")

    # Calculate Type II error delta = 1 - power (relative to baseline)
    # If baseline power is < 1.0, we normalize the delta relative to the baseline?
    # The task says "relative to 30m baseline". Usually Type II error is 1-power.
    # If the baseline itself has power < 1, the "delta relative to baseline"
    # implies the loss of power compared to the baseline's performance.
    # Interpretation: Delta = (Baseline_Power - Current_Power) / Baseline_Power
    # OR simply the absolute difference if baseline is treated as 100% potential.
    # Given "1 - power" is the standard definition, we calculate 1 - power for each row.
    # To make it "relative to baseline", we compute the difference in power loss.
    # Let's stick to the literal: Type II Error = 1 - Power.
    # The "delta relative to baseline" likely means the increase in Type II error
    # compared to the baseline's Type II error.
    # Delta = (1 - current_power) - (1 - baseline_power) = baseline_power - current_power.

    df['type2_error'] = 1.0 - df['power']
    baseline_type2 = 1.0 - baseline_power
    df['type2_error_delta'] = df['type2_error'] - baseline_type2

    # Sort by resolution for readability
    df['res_num'] = df['resolution'].apply(get_res_num)
    df = df.sort_values('res_num').drop(columns=['res_num'])

    logger.info("Type II error delta calculation complete.")
    return df

def main():
    logger = get_logger(__name__)
    logger.info("Starting Type II Error Delta Analysis (T030)")

    # Paths
    project_root = Path(__file__).resolve().parent.parent
    power_csv_path = project_root / "data" / "results" / "power_results.csv"
    output_csv_path = project_root / "data" / "results" / "type2_error_analysis.csv"

    try:
        df = calculate_type2_error_delta(str(power_csv_path))
        df.to_csv(output_csv_path, index=False)
        logger.info(f"Results saved to {output_csv_path}")

        # Print summary to stdout for quick verification
        print(f"{'Resolution':<10} | {'Power':<8} | {'Type II Error':<15} | {'Delta':<10}")
        print("-" * 50)
        for _, row in df.iterrows():
            print(f"{row['resolution']:<10} | {row['power']:.4f}   | {row['type2_error']:.4f}          | {row['type2_error_delta']:.4f}")

    except FileNotFoundError as e:
        logger.error(f"Input file missing: {e}")
        raise
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()
