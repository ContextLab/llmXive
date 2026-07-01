import json
import os
import sys
import random
from pathlib import Path
from datetime import datetime

# Optional dependencies
try:
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
except ImportError:
    print("ERROR: This adaptation requires pandas, numpy, and matplotlib.")
    print("Run: pip install pandas numpy matplotlib")
    sys.exit(1)

# --- Configuration ---
DATA_DIR = Path("data")
FIGURES_DIR = Path("figures")
DATA_DIR.mkdir(exist_ok=True)
FIGURES_DIR.mkdir(exist_ok=True)

# Thresholds from the original paper's `audit.py`
MIN_ROWS = 50
MIN_NON_NULL_RATE = 0.5
LARGE_FILE_BYTES = 50 * 1024 * 1024  # 50 MB

def generate_synthetic_dataset(seed: int, rows: int, corruption_rate: float = 0.0):
    """
    Generates a synthetic dataset mimicking OWID/Climate data structure.
    This replaces the need to download real large-scale datasets for the CPU run.
    """
    random.seed(seed)
    np.random.seed(seed)
    
    entities = ["USA", "China", "Germany", "Brazil", "India", "Japan", "UK", "France", "Canada", "Australia"]
    years = list(range(1950, 2024))
    
    data = []
    for _ in range(rows):
        ent = random.choice(entities)
        yr = random.choice(years)
        
        # Base metric: CO2 emissions (random walk with noise)
        base = 100.0 if ent == "China" else 50.0
        value = base + np.random.normal(0, 10)
        
        # Apply corruption
        if random.random() < corruption_rate:
            value = np.nan
        
        data.append({
            "Entity": ent,
            "Code": ent[:3].upper(),
            "Year": yr,
            "CO2_Emissions_tonnes": round(value, 2) if not pd.isna(value) else np.nan,
            "Population_millions": round(np.random.uniform(1, 350), 2)
        })
    
    return pd.DataFrame(data)

def inspect_csv(df: pd.DataFrame, file_name: str = "synthetic_data.csv"):
    """
    Replicates the logic from `pro/skills/find-data/tools/audit.py`
    to check the 4 completeness gates.
    """
    entry = {
        "file": file_name,
        "format": "csv",
        "rows": len(df),
        "cols": list(df.columns),
        "gates": {},
        "metrics": {}
    }

    # Gate 1: Format & Readability (Implicit, passed if we got here)
    entry["gates"]["gate_1_readable"] = True

    # Gate 2: Row Count
    entry["gates"]["gate_2_rows"] = len(df) >= MIN_ROWS
    entry["metrics"]["row_count"] = len(df)

    # Gate 3: Non-Null Rate on Primary Metric
    # Identify metric columns (not Entity, Code, Year)
    metric_cols = [c for c in df.columns if c not in ("Entity", "Code", "Year")]
    if metric_cols:
        primary_metric = metric_cols[0]
        non_null_count = df[primary_metric].notna().sum()
        non_null_rate = non_null_count / len(df) if len(df) > 0 else 0.0
        entry["gates"]["gate_3_non_null"] = non_null_rate >= MIN_NON_NULL_RATE
        entry["metrics"]["primary_metric"] = primary_metric
        entry["metrics"]["non_null_rate"] = round(non_null_rate, 3)
    else:
        entry["gates"]["gate_3_non_null"] = False
        entry["metrics"]["primary_metric"] = None
        entry["metrics"]["non_null_rate"] = 0.0

    # Gate 4: Year Range (Check if we have historical data)
    if "Year" in df.columns:
        min_year = int(df["Year"].min())
        max_year = int(df["Year"].max())
        entry["gates"]["gate_4_year_range"] = (max_year - min_year) >= 10
        entry["metrics"]["year_span"] = max_year - min_year
        entry["metrics"]["year_min"] = min_year
        entry["metrics"]["year_max"] = max_year
    else:
        entry["gates"]["gate_4_year_range"] = False
        entry["metrics"]["year_span"] = 0

    # Overall Verdict
    all_gates_pass = all(entry["gates"].values())
    entry["verdict"] = "PASS" if all_gates_pass else "FAIL"
    
    return entry

def run_discovery_simulation():
    """
    Simulates the `browse_local.py` logic by scanning our synthetic datasets.
    """
    datasets = []
    
    # Generate 5 synthetic datasets with varying quality
    seeds = [101, 102, 103, 104, 105]
    corruption_rates = [0.0, 0.1, 0.3, 0.6, 0.0] # 0.6 will fail the non-null gate
    row_counts = [200, 200, 200, 200, 40]       # 40 rows will fail the row gate
    
    for i, (seed, corr, rows) in enumerate(zip(seeds, corruption_rates, row_counts)):
        df = generate_synthetic_dataset(seed, rows, corr)
        audit_result = inspect_csv(df, f"climate_dataset_{i+1}.csv")
        audit_result["topic"] = "Climate & Environment"
        audit_result["source"] = "Synthetic_Economist_Clone"
        datasets.append(audit_result)
        
        # Write individual audit file (simulating the tool output)
        with open(DATA_DIR / f"audit_{i+1}.json", "w") as f:
            json.dump(audit_result, f, indent=2)

    return datasets

def generate_visualization(results: list[dict]):
    """
    Creates a plot showing the distribution of quality metrics.
    """
    rows = [r["metrics"]["row_count"] for r in results]
    non_nulls = [r["metrics"]["non_null_rate"] for r in results]
    verdicts = [1 if r["verdict"] == "PASS" else 0 for r in results]
    
    plt.figure(figsize=(10, 6))
    x = range(len(results))
    
    # Plot Row Count
    plt.subplot(2, 1, 1)
    plt.bar(x, rows, color='skyblue', label='Row Count')
    plt.axhline(y=MIN_ROWS, color='red', linestyle='--', label=f'Min Rows ({MIN_ROWS})')
    plt.ylabel('Rows')
    plt.title('Dataset Completeness: Row Count & Non-Null Rate')
    plt.legend()
    plt.grid(axis='y', alpha=0.3)
    
    # Plot Non-Null Rate
    plt.subplot(2, 1, 2)
    plt.bar(x, non_nulls, color='lightgreen', label='Non-Null Rate')
    plt.axhline(y=MIN_NON_NULL_RATE, color='red', linestyle='--', label=f'Min Rate ({MIN_NON_NULL_RATE})')
    plt.ylabel('Non-Null Rate')
    plt.xlabel('Dataset Index')
    plt.xticks(x, [f"DS-{i+1}" for i in x])
    plt.legend()
    plt.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "quality_distribution.png", dpi=150)
    plt.close()

def main():
    print("=== Data2Story Adaptation: Completeness Audit ===")
    print("Running simulation of 'Find-Data' and 'Inspector' gates...")
    
    # 1. Generate and Audit Datasets
    results = run_discovery_simulation()
    
    # 2. Aggregate Results
    pass_count = sum(1 for r in results if r["verdict"] == "PASS")
    total_count = len(results)
    
    summary = {
        "timestamp": datetime.now().isoformat(),
        "total_datasets_scanned": total_count,
        "datasets_passing_all_gates": pass_count,
        "gate_success_rate": round(pass_count / total_count, 2) if total_count > 0 else 0,
        "thresholds_used": {
            "min_rows": MIN_ROWS,
            "min_non_null_rate": MIN_NON_NULL_RATE
        },
        "individual_results": results
    }
    
    # 3. Write Outputs
    # A. Summary Report
    with open(DATA_DIR / "audit_report.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(f"✓ Wrote summary to {DATA_DIR}/audit_report.json")
    
    # B. Visualization
    generate_visualization(results)
    print(f"✓ Wrote visualization to {FIGURES_DIR}/quality_distribution.png")
    
    # 4. Print Console Summary
    print("\n--- Results Summary ---")
    for r in results:
        status = "✅ PASS" if r["verdict"] == "PASS" else "❌ FAIL"
        print(f"{r['file']}: {status} (Rows: {r['metrics']['row_count']}, Non-Null: {r['metrics']['non_null_rate']})")
    
    print(f"\nTotal Pass Rate: {summary['gate_success_rate'] * 100}%")
    print("Adaptation complete. Artifacts written to data/ and figures/.")

if __name__ == "__main__":
    main()
