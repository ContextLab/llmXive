import os
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
from utils.logger import get_logger
from config.settings import get_settings
from datetime import datetime

logger = get_logger(__name__)

class ReportGenerator:
    def __init__(self, processed_dir: Path, figures_dir: Path):
        self.processed_dir = processed_dir
        self.figures_dir = figures_dir
        self.report_path = processed_dir / "report_summary.txt"

    def load_metrics(self) -> pd.DataFrame:
        path = self.processed_dir / "metrics_summary.csv"
        if path.exists():
            return pd.read_csv(path)
        return pd.DataFrame()

    def load_cleaned_data(self) -> pd.DataFrame:
        path = self.processed_dir / "cleaned_sessions.csv"
        if path.exists():
            return pd.read_csv(path)
        return pd.DataFrame()

    def load_power_flags(self) -> List[str]:
        path = self.processed_dir / "power_flags.txt"
        if path.exists():
            return path.read_text().splitlines()
        return []

    def generate_report(self):
        """Generates the summary report text file."""
        metrics_df = self.load_metrics()
        data_df = self.load_cleaned_data()
        power_flags = self.load_power_flags()
        
        lines = []
        lines.append("Research Study Summary Report")
        lines.append("=" * 50)
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # 1. Participant Statistics
        lines.append("1. Participant Statistics")
        lines.append("-" * 30)
        if not data_df.empty:
            lines.append(f"Total Sessions Analyzed: {len(data_df)}")
            if 'disability_type' in data_df.columns:
                lines.append(f"Disability Types: {data_df['disability_type'].value_counts().to_dict()}")
            if 'interface_type' in data_df.columns:
                lines.append(f"Interface Distribution: {data_df['interface_type'].value_counts().to_dict()}")
        else:
            lines.append("No data available.")
        lines.append("")

        # 2. Statistical Results
        lines.append("2. Statistical Results (ANOVA)")
        lines.append("-" * 30)
        if not metrics_df.empty:
            for _, row in metrics_df.iterrows():
                lines.append(f"Metric: {row['metric']}")
                lines.append(f"  F-statistic: {row['F-statistic']:.4f}")
                lines.append(f"  p-value: {row['p-value']:.4f}")
                lines.append(f"  Adjusted p-value: {row['adjusted p-value']:.4f}")
                lines.append(f"  Effect Size: {row['effect size']:.4f}")
                lines.append(f"  Method: {row['method']}")
                lines.append("")
        else:
            lines.append("No statistical results available.")
        lines.append("")

        # 3. Power Analysis
        lines.append("3. Power Analysis & Limitations")
        lines.append("-" * 30)
        if power_flags:
            for flag in power_flags:
                lines.append(f"  - {flag}")
        else:
            lines.append("  No power flags generated.")
        lines.append("")

        # 4. Exclusions
        lines.append("4. Exclusion Summary")
        lines.append("-" * 30)
        exclusion_log = self.processed_dir / "exclusion_log.txt"
        if exclusion_log.exists():
            lines.append(exclusion_log.read_text())
        else:
            lines.append("No exclusion log found.")
        lines.append("")

        # 5. Figures
        lines.append("5. Generated Figures")
        lines.append("-" * 30)
        if self.figures_dir.exists():
            plots = list(self.figures_dir.glob("*.png"))
            for p in plots:
                lines.append(f"  - {p.name}")
        else:
            lines.append("  No figures directory found.")
        
        # Write to file
        with open(self.report_path, "w") as f:
            f.write("\n".join(lines))
        
        logger.info(f"Report generated: {self.report_path}")

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--processed", type=str, required=True)
    parser.add_argument("--figures", type=str, required=True)
    args = parser.parse_args()
    
    gen = ReportGenerator(Path(args.processed), Path(args.figures))
    gen.generate_report()

if __name__ == "__main__":
    main()
