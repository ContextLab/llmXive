"""
Metric Aggregator for Quality Assessment Pipeline (T032)

Aggregates individual quality metrics (pass_rate, complexity, coverage, static_warnings)
per submission and stores them in the SQLite database.
"""
import os
import sys
import json
import logging
import sqlite3
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.db_schema import get_connection
from data.models import Metric
from quality.pass_rate import calculate_pass_rate
from quality.complexity import compute_cyclomatic_complexity
from quality.coverage import compute_coverage
from quality.static_analysis import analyze_static_warnings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MetricAggregator:
    """Aggregates quality metrics for a submission and persists to database."""

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the aggregator.

        Args:
            db_path: Path to SQLite database. Uses default from settings if None.
        """
        self.db_path = db_path or os.environ.get('DATABASE_PATH', 'data/experiment.db')
        self.conn: Optional[sqlite3.Connection] = None

    def _get_connection(self) -> sqlite3.Connection:
        """Get or create database connection."""
        if self.conn is None:
            self.conn = get_connection(self.db_path)
        return self.conn

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def compute_all_metrics(self, submission_id: str, code_content: str, language: str = 'python') -> Dict[str, Any]:
        """
        Compute all quality metrics for a submission.

        Args:
            submission_id: Unique identifier for the submission.
            code_content: The submitted code as a string.
            language: Programming language ('python' or 'java').

        Returns:
            Dictionary containing all computed metrics.
        """
        logger.info(f"Computing metrics for submission {submission_id}")

        metrics = {
            'submission_id': submission_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'language': language,
            'pass_rate': None,
            'cyclomatic_complexity': None,
            'coverage': None,
            'static_warnings': None,
            'status': 'pending'
        }

        try:
            # 1. Pass Rate (HumanEval)
            if language == 'python':
                pass_rate_result = calculate_pass_rate(code_content)
                metrics['pass_rate'] = pass_rate_result.get('pass_rate')
                metrics['tests_passed'] = pass_rate_result.get('tests_passed')
                metrics['tests_total'] = pass_rate_result.get('tests_total')
            else:
                logger.warning(f"Pass rate calculation not implemented for {language}")
                metrics['pass_rate'] = None

            # 2. Cyclomatic Complexity
            complexity_result = compute_cyclomatic_complexity(code_content)
            metrics['cyclomatic_complexity'] = complexity_result.get('complexity')
            metrics['complexity_breakdown'] = complexity_result.get('breakdown', {})

            # 3. Test Coverage
            if language == 'python':
                coverage_result = compute_coverage(code_content)
                metrics['coverage'] = coverage_result.get('coverage_percent')
                metrics['lines_covered'] = coverage_result.get('lines_covered')
                metrics['lines_total'] = coverage_result.get('lines_total')
            else:
                logger.warning(f"Coverage calculation not implemented for {language}")
                metrics['coverage'] = None

            # 4. Static Analysis Warnings
            static_result = analyze_static_warnings(code_content, language)
            metrics['static_warnings'] = static_result.get('warning_count')
            metrics['static_details'] = static_result.get('details', [])

            # Determine overall status
            metrics['status'] = 'completed'

        except Exception as e:
            logger.error(f"Error computing metrics for {submission_id}: {str(e)}")
            metrics['status'] = 'error'
            metrics['error_message'] = str(e)

        return metrics

    def store_metrics(self, metrics: Dict[str, Any]) -> bool:
        """
        Store computed metrics in the database.

        Args:
            metrics: Dictionary of computed metrics.

        Returns:
            True if successful, False otherwise.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Ensure Metric table exists (should be created by schema init)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Metric (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    submission_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    language TEXT,
                    pass_rate REAL,
                    cyclomatic_complexity INTEGER,
                    coverage REAL,
                    static_warnings INTEGER,
                    status TEXT,
                    tests_passed INTEGER,
                    tests_total INTEGER,
                    complexity_breakdown TEXT,
                    lines_covered INTEGER,
                    lines_total INTEGER,
                    static_details TEXT,
                    error_message TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Insert or update metrics
            cursor.execute("""
                INSERT OR REPLACE INTO Metric (
                    submission_id, timestamp, language, pass_rate,
                    cyclomatic_complexity, coverage, static_warnings,
                    status, tests_passed, tests_total, complexity_breakdown,
                    lines_covered, lines_total, static_details, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metrics['submission_id'],
                metrics['timestamp'],
                metrics['language'],
                metrics.get('pass_rate'),
                metrics.get('cyclomatic_complexity'),
                metrics.get('coverage'),
                metrics.get('static_warnings'),
                metrics.get('status'),
                metrics.get('tests_passed'),
                metrics.get('tests_total'),
                json.dumps(metrics.get('complexity_breakdown', {})),
                metrics.get('lines_covered'),
                metrics.get('lines_total'),
                json.dumps(metrics.get('static_details', [])),
                metrics.get('error_message')
            ))

            conn.commit()
            logger.info(f"Stored metrics for submission {metrics['submission_id']}")
            return True

        except Exception as e:
            logger.error(f"Failed to store metrics: {str(e)}")
            return False

    def get_metrics(self, submission_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve stored metrics for a submission.

        Args:
            submission_id: The submission ID to look up.

        Returns:
            Dictionary of metrics or None if not found.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT submission_id, timestamp, language, pass_rate,
                       cyclomatic_complexity, coverage, static_warnings,
                       status, tests_passed, tests_total, complexity_breakdown,
                       lines_covered, lines_total, static_details, error_message
                FROM Metric
                WHERE submission_id = ?
            """, (submission_id,))

            row = cursor.fetchone()
            if not row:
                return None

            return {
                'submission_id': row[0],
                'timestamp': row[1],
                'language': row[2],
                'pass_rate': row[3],
                'cyclomatic_complexity': row[4],
                'coverage': row[5],
                'static_warnings': row[6],
                'status': row[7],
                'tests_passed': row[8],
                'tests_total': row[9],
                'complexity_breakdown': json.loads(row[10]) if row[10] else {},
                'lines_covered': row[11],
                'lines_total': row[12],
                'static_details': json.loads(row[13]) if row[13] else [],
                'error_message': row[14]
            }

        except Exception as e:
            logger.error(f"Failed to retrieve metrics: {str(e)}")
            return None

    def aggregate_all_pending(self) -> int:
        """
        Aggregate metrics for all submissions that haven't been processed yet.

        Returns:
            Number of submissions processed.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Get all submissions without metrics or with pending status
            cursor.execute("""
                SELECT s.id, s.code_content, s.language
                FROM Submission s
                LEFT JOIN Metric m ON s.id = m.submission_id
                WHERE m.submission_id IS NULL OR m.status = 'pending'
            """)

            submissions = cursor.fetchall()
            processed = 0

            for sub_id, code_content, language in submissions:
                metrics = self.compute_all_metrics(sub_id, code_content, language)
                if self.store_metrics(metrics):
                    processed += 1

            return processed

        except Exception as e:
            logger.error(f"Error in bulk aggregation: {str(e)}")
            return 0


def main():
    """Main entry point for CLI usage."""
    import argparse

    parser = argparse.ArgumentParser(description='Aggregate quality metrics for submissions')
    parser.add_argument('--submission-id', type=str, help='Specific submission ID to process')
    parser.add_argument('--code', type=str, help='Code content to analyze (if no submission ID)')
    parser.add_argument('--language', type=str, default='python', help='Programming language')
    parser.add_argument('--bulk', action='store_true', help='Process all pending submissions')
    parser.add_argument('--db', type=str, help='Database path')

    args = parser.parse_args()

    aggregator = MetricAggregator(db_path=args.db)

    try:
        if args.bulk:
            count = aggregator.aggregate_all_pending()
            print(f"Processed {count} submissions")
        elif args.submission_id:
            metrics = aggregator.get_metrics(args.submission_id)
            if metrics:
                print(json.dumps(metrics, indent=2))
            else:
                print(f"No metrics found for submission {args.submission_id}")
        elif args.code:
            metrics = aggregator.compute_all_metrics(
                args.submission_id or 'manual',
                args.code,
                args.language
            )
            aggregator.store_metrics(metrics)
            print(json.dumps(metrics, indent=2))
        else:
            parser.print_help()

    finally:
        aggregator.close()


if __name__ == '__main__':
    main()