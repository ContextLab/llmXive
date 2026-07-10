"""
Report Generator Module for PROJ-015.

Generates the final summary report (data/processed/report_summary.txt)
containing actual N, power limitation flags, and exclusion reasons.
"""
import os
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
from utils.logger import get_logger
from config.settings import get_settings

logger = get_logger(__name__)

class ReportGenerator:
    """Generates summary reports based on analysis results and raw data logs."""

    def __init__(self, settings: Optional[Dict[str, Any]] = None):
        self.settings = settings or get_settings()
        self.project_root = Path(self.settings.get("PROJECT_ROOT", "."))
        self.raw_data_dir = self.project_root / "data" / "raw"
        self.processed_data_dir = self.project_root / "data" / "processed"
        self.metrics_summary_path = self.processed_data_dir / "metrics_summary.csv"
        self.output_path = self.processed_data_dir / "report_summary.txt"

    def _load_raw_sessions(self) -> List[Dict[str, Any]]:
        """Load all session JSON files from data/raw/."""
        sessions = []
        if not self.raw_data_dir.exists():
            logger.warning(f"Raw data directory not found: {self.raw_data_dir}")
            return sessions

        for json_file in self.raw_data_dir.glob("session_*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    sessions.append(data)
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Failed to load {json_file}: {e}")
        return sessions

    def _calculate_power_flags(self, n_total: int, n_subgroups: Dict[str, int]) -> List[str]:
        """
        Determine power limitation flags.
        Standard threshold for adequate power in this context is n >= 30 for the total,
        and n >= 15 (or similar heuristic) for subgroups to ensure stability.
        Returns a list of flag strings.
        """
        flags = []
        
        # Check total N
        if n_total < 30:
            flags.append(f"WARNING: Total sample size (N={n_total}) is below recommended threshold (N>=30) for robust statistical power.")
        
        # Check subgroups
        for group_name, count in n_subgroups.items():
            if count < 15:
                flags.append(f"WARNING: Subgroup '{group_name}' (N={count}) is underpowered for reliable subgroup analysis.")
            
        return flags

    def generate_report(self) -> Path:
        """
        Generate the summary report file.
        
        The report includes:
        1. Actual N achieved (total and by subgroup if available).
        2. Power limitation flags.
        3. Exclusion reasons for incomplete sessions.
        
        Returns the path to the generated report.
        """
        # Ensure output directory exists
        self.processed_data_dir.mkdir(parents=True, exist_ok=True)

        # Load raw sessions to determine N and exclusions
        sessions = self._load_raw_sessions()
        
        total_sessions = len(sessions)
        excluded_sessions = [s for s in sessions if s.get('status') == 'incomplete']
        included_sessions = [s for s in sessions if s.get('status') != 'incomplete']
        
        actual_n = len(included_sessions)
        
        # Analyze subgroups based on disability_type if present
        # Assuming 'Participant' data is nested in 'participant' or similar
        subgroup_counts: Dict[str, int] = {}
        for s in included_sessions:
            # Try to find disability type in participant data
            participant = s.get('participant', {})
            if not participant:
                # Fallback if structure is flat
                participant = s
            
            dtype = participant.get('disability_type', 'Unknown')
            subgroup_counts[dtype] = subgroup_counts.get(dtype, 0) + 1

        # Calculate power flags
        power_flags = self._calculate_power_flags(actual_n, subgroup_counts)

        # Collect exclusion reasons
        exclusion_reasons = []
        for s in excluded_sessions:
            reason = s.get('dropout_reason', 'Unknown reason')
            session_id = s.get('session_id', 'N/A')
            exclusion_reasons.append(f"- Session {session_id}: {reason}")
        
        if not exclusion_reasons:
            exclusion_reasons.append("- None (all sessions completed)")

        # Construct report content
        report_lines = [
            "=" * 60,
            "RESEARCH STUDY SUMMARY REPORT",
            "Project: Improving Accessibility and Usability of Complex Systems",
            "=" * 60,
            "",
            "1. SAMPLE SIZE STATISTICS",
            "-" * 40,
            f"Total Sessions Logged: {total_sessions}",
            f"Excluded Sessions: {len(excluded_sessions)}",
            f"Actual N (Included): {actual_n}",
            ""
        ]

        if subgroup_counts:
            report_lines.append("Subgroup Breakdown (Included):")
            for group, count in sorted(subgroup_counts.items()):
                report_lines.append(f"  - {group}: {count}")
            report_lines.append("")

        report_lines.append("2. POWER LIMITATION FLAGS",)
        report_lines.append("-" * 40)
        if power_flags:
            for flag in power_flags:
                report_lines.append(flag)
        else:
            report_lines.append("No power limitations detected based on current thresholds.")
        report_lines.append("")

        report_lines.append("3. EXCLUSION REASONS",)
        report_lines.append("-" * 40)
        for reason in exclusion_reasons:
            report_lines.append(reason)
        report_lines.append("")
        report_lines.append("=" * 60)
        report_lines.append("END OF REPORT")
        report_lines.append("=" * 60)

        report_content = "\n".join(report_lines)

        # Write to file
        with open(self.output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)

        logger.info(f"Report generated successfully at: {self.output_path}")
        return self.output_path

def main():
    """Entry point for the report generator script."""
    logger.info("Starting Report Generation (T030)...")
    generator = ReportGenerator()
    try:
        output_file = generator.generate_report()
        print(f"Report generated: {output_file}")
    except Exception as e:
        logger.error(f"Failed to generate report: {e}")
        raise

if __name__ == "__main__":
    main()
