import os
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
from utils.logger import get_logger
from config.settings import get_settings

logger = get_logger(__name__)

class ReportGenerator:
    """
    Generates the final summary report text file including:
    1. Actual N achieved
    2. Power limitation flags for underpowered subgroups
    3. Exclusion reasons for incomplete sessions
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.settings = get_settings()
        self.config = config or {}
        self.project_root = Path(self.settings.project_root)
        self.data_raw_dir = self.project_root / self.settings.data_raw_dir
        self.data_processed_dir = self.project_root / self.settings.data_processed_dir

        # Ensure processed directory exists
        self.data_processed_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"ReportGenerator initialized. Raw data: {self.data_raw_dir}, Processed: {self.data_processed_dir}")

    def _load_raw_sessions(self) -> List[Dict[str, Any]]:
        """Load all raw session JSON files."""
        sessions = []
        pattern = self.data_raw_dir / "session_*.json"
        files = list(self.data_raw_dir.glob(pattern.name))
        
        if not files:
            logger.warning(f"No session files found in {self.data_raw_dir}")
            return sessions

        for file_path in files:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    sessions.append(data)
            except Exception as e:
                logger.error(f"Failed to load session file {file_path}: {e}")
        
        return sessions

    def _calculate_statistics(self, sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate N, exclusion reasons, and power flags.
        """
        total_sessions = len(sessions)
        completed_sessions = [s for s in sessions if s.get('status') == 'complete']
        incomplete_sessions = [s for s in sessions if s.get('status') != 'complete']
        
        n_total = total_sessions
        n_completed = len(completed_sessions)
        n_incomplete = len(incomplete_sessions)

        exclusion_reasons = []
        for s in incomplete_sessions:
            reason = s.get('dropout_reason', 'Unknown')
            exclusion_reasons.append({
                'session_id': s.get('session_id', 'N/A'),
                'reason': reason,
                'participant_id': s.get('participant_id', 'N/A')
            })

        # Power analysis logic
        # Assuming a standard power analysis for a medium effect size (Cohen's d = 0.5)
        # with alpha = 0.05, power = 0.80 requires N ~ 34 per group for independent,
        # or fewer for repeated measures (e.g., ~17-20 depending on correlation).
        # We flag if N < 20 per interface type (conservative for repeated measures).
        
        interface_counts = {}
        for s in completed_sessions:
            # Assuming interface_variant is stored in the session or derived from sequence
            # In our data model, sequence is stored, so we check the sequence for the interface type
            # But for simplicity, let's assume 'interface_variant' is a field or we infer from 'sequence'
            # Looking at T014/T019, 'interface_variant' might be logged. 
            # Let's check for 'sequence' which contains the order (e.g., ['Traditional', 'Explainable'])
            sequence = s.get('sequence', [])
            for iface in sequence:
                interface_counts[iface] = interface_counts.get(iface, 0) + 1

        power_flags = []
        min_power_n = 20  # Threshold for power flagging (adjust based on actual power calc if available)
        
        for iface, count in interface_counts.items():
            if count < min_power_n:
                power_flags.append({
                    'interface': iface,
                    'n': count,
                    'threshold': min_power_n,
                    'message': f"Underpowered: N={count} < {min_power_n} for interface '{iface}'"
                })

        return {
            'n_total': n_total,
            'n_completed': n_completed,
            'n_incomplete': n_incomplete,
            'exclusion_reasons': exclusion_reasons,
            'power_flags': power_flags,
            'interface_counts': interface_counts
        }

    def generate_report(self, output_path: Optional[str] = None) -> str:
        """
        Generate the summary report and write to disk.
        Returns the path to the generated report.
        """
        logger.info("Starting report generation...")
        
        sessions = self._load_raw_sessions()
        stats = self._calculate_statistics(sessions)

        report_lines = [
            "=" * 60,
            "RESEARCH STUDY SUMMARY REPORT",
            "=" * 60,
            "",
            "1. PARTICIPANT & SESSION STATISTICS",
            "-" * 40,
            f"Total Sessions Initiated: {stats['n_total']}",
            f"Completed Sessions: {stats['n_completed']}",
            f"Incomplete/Excluded Sessions: {stats['n_incomplete']}",
            "",
            "2. EXCLUSION REASONS (Incomplete Sessions)",
            "-" * 40,
        ]

        if stats['exclusion_reasons']:
            for reason in stats['exclusion_reasons']:
                report_lines.append(
                    f"  - Session {reason['session_id']} (Participant {reason['participant_id']}): {reason['reason']}"
                )
        else:
            report_lines.append("  No incomplete sessions recorded.")

        report_lines.extend([
            "",
            "3. POWER ANALYSIS & LIMITATIONS",
            "-" * 40,
        ])

        if stats['power_flags']:
            report_lines.append("  ⚠️ POWER LIMITATIONS DETECTED:")
            for flag in stats['power_flags']:
                report_lines.append(f"    - {flag['message']}")
            report_lines.append("")
            report_lines.append("  Note: Small sample sizes may reduce statistical power to detect medium effects.")
        else:
            report_lines.append("  ✓ Sample sizes appear sufficient for power analysis (N >= 20 per interface).")

        report_lines.extend([
            "",
            "4. INTERFACE DISTRIBUTION (Completed Sessions)",
            "-" * 40,
        ])

        for iface, count in sorted(stats['interface_counts'].items()):
            report_lines.append(f"  - {iface}: {count} sessions")

        report_lines.extend([
            "",
            "=" * 60,
            f"Report Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 60,
        ])

        report_text = "\n".join(report_lines)

        # Determine output path
        if output_path is None:
            output_path = self.data_processed_dir / "report_summary.txt"
        else:
            output_path = Path(output_path)
            if not output_path.parent.exists():
                output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            f.write(report_text)

        logger.info(f"Report generated successfully at: {output_path}")
        return str(output_path)

    def main():
        """CLI entry point."""
        generator = ReportGenerator()
        try:
            report_path = generator.generate_report()
            print(f"Report generated: {report_path}")
            return 0
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            return 1

if __name__ == "__main__":
    import sys
    sys.exit(ReportGenerator.main())
