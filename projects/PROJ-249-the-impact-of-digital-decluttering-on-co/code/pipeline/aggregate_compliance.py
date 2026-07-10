"""
Compliance Aggregation Script (T027)

Calculates daily and weekly compliance scores from parsed compliance logs.
Integrates with the rules engine to determine compliance status for each entry.
"""
import os
import csv
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import defaultdict

# Import from existing project modules
from compliance.parse_logs import parse_csv_logs, validate_and_normalize
from compliance.rules_engine import check_compliance_rules, ComplianceResult
from config.env_config import get_path, get_config
from utils.random_seed import get_seed


def calculate_daily_scores(
    parsed_logs: List[Dict[str, Any]],
    rules_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Calculate compliance scores for each day based on parsed logs.

    Args:
        parsed_logs: List of normalized log entries from parse_logs
        rules_config: Configuration for compliance rules (optional)

    Returns:
        Dictionary mapping date strings to daily compliance stats
    """
    # Group logs by participant and date
    daily_data: Dict[str, Dict[str, List[Dict]]] = defaultdict(lambda: defaultdict(list))

    for log in parsed_logs:
        participant_id = log.get('participant_id')
        log_date = log.get('date')
        if participant_id and log_date:
            daily_data[participant_id][log_date].append(log)

    results = {}

    # Default rules if not provided
    if rules_config is None:
        config = get_config()
        rules_config = {
            'social_media_max_minutes': config.get('social_media_max_minutes', 30),
            'news_allowed': config.get('news_allowed', False),
            'notifications_must_be_off': config.get('notifications_must_be_off', True)
        }

    for participant_id, dates in daily_data.items():
        for date_str, logs in dates.items():
            # Check compliance for each log entry on this day
            daily_compliance_checks = []
            for log in logs:
                # Prepare data for rules engine
                check_data = {
                    'social_media_minutes': log.get('social_media_minutes', 0),
                    'news_minutes': log.get('news_minutes', 0),
                    'notifications_off': log.get('notifications_off', True),
                    'date': log.get('date'),
                    'participant_id': participant_id
                }
                result = check_compliance_rules(check_data, rules_config)
                daily_compliance_checks.append(result)

            # Aggregate daily stats
            compliant_count = sum(1 for r in daily_compliance_checks if r.is_compliant)
            total_logs = len(daily_compliance_checks)
            compliance_rate = compliant_count / total_logs if total_logs > 0 else 0.0

            # Calculate average minutes for non-compliant categories
            total_social_media = sum(log.get('social_media_minutes', 0) for log in logs)
            total_news = sum(log.get('news_minutes', 0) for log in logs)

            results[f"{participant_id}_{date_str}"] = {
                'participant_id': participant_id,
                'date': date_str,
                'total_logs': total_logs,
                'compliant_logs': compliant_count,
                'compliance_rate': round(compliance_rate, 4),
                'total_social_media_minutes': total_social_media,
                'total_news_minutes': total_news,
                'is_compliant_day': compliance_rate == 1.0,
                'violations': [
                    {
                        'log_index': i,
                        'violation_type': r.violations
                    }
                    for i, r in enumerate(daily_compliance_checks)
                    if r.violations
                ]
            }

    return results


def calculate_weekly_scores(
    daily_scores: Dict[str, Dict[str, Any]]
) -> Dict[str, Dict[str, Any]]:
    """
    Aggregate daily scores into weekly compliance metrics.

    Args:
        daily_scores: Output from calculate_daily_scores

    Returns:
        Dictionary mapping participant-week keys to weekly stats
    """
    # Group by participant and ISO week
    weekly_data: Dict[str, Dict[int, List[Dict]]] = defaultdict(lambda: defaultdict(list))

    for key, stats in daily_scores.items():
        participant_id = stats['participant_id']
        date_str = stats['date']
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            iso_cal = date_obj.isocalendar()
            week_key = f"{iso_cal[0]}-W{iso_cal[1]:02d}"  # YYYY-Www
            weekly_data[participant_id][week_key].append(stats)
        except ValueError:
            continue

    results = {}
    for participant_id, weeks in weekly_data.items():
        for week_key, days in weeks.items():
            if not days:
                continue

            total_days = len(days)
            compliant_days = sum(1 for d in days if d['is_compliant_day'])
            weekly_compliance_rate = compliant_days / total_days

            # Aggregate minutes
            total_social_media = sum(d['total_social_media_minutes'] for d in days)
            total_news = sum(d['total_news_minutes'] for d in days)
            avg_daily_social_media = total_social_media / total_days
            avg_daily_news = total_news / total_days

            results[f"{participant_id}_{week_key}"] = {
                'participant_id': participant_id,
                'week': week_key,
                'total_days_logged': total_days,
                'compliant_days': compliant_days,
                'weekly_compliance_rate': round(weekly_compliance_rate, 4),
                'total_social_media_minutes': total_social_media,
                'total_news_minutes': total_news,
                'avg_daily_social_media_minutes': round(avg_daily_social_media, 2),
                'avg_daily_news_minutes': round(avg_daily_news, 2),
                'is_compliant_week': weekly_compliance_rate == 1.0
            }

    return results


def write_aggregation_results(
    daily_scores: Dict[str, Dict[str, Any]],
    weekly_scores: Dict[str, Dict[str, Any]],
    output_dir: Optional[Path] = None
) -> Dict[str, str]:
    """
    Write aggregation results to CSV and JSON files.

    Args:
        daily_scores: Daily compliance metrics
        weekly_scores: Weekly compliance metrics
        output_dir: Output directory (defaults to data/processed)

    Returns:
        Dictionary of output file paths
    """
    if output_dir is None:
        output_dir = get_path('processed_data')

    output_dir.mkdir(parents=True, exist_ok=True)

    # Write daily scores
    daily_csv_path = output_dir / 'daily_compliance_scores.csv'
    daily_json_path = output_dir / 'daily_compliance_scores.json'

    if daily_scores:
        # CSV output
        with open(daily_csv_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = [
                'participant_id', 'date', 'total_logs', 'compliant_logs',
                'compliance_rate', 'total_social_media_minutes', 'total_news_minutes',
                'is_compliant_day'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for stats in daily_scores.values():
                row = {k: v for k, v in stats.items() if k in fieldnames}
                writer.writerow(row)

        # JSON output
        with open(daily_json_path, 'w', encoding='utf-8') as f:
            json.dump(daily_scores, f, indent=2)

    # Write weekly scores
    weekly_csv_path = output_dir / 'weekly_compliance_scores.csv'
    weekly_json_path = output_dir / 'weekly_compliance_scores.json'

    if weekly_scores:
        # CSV output
        with open(weekly_csv_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = [
                'participant_id', 'week', 'total_days_logged', 'compliant_days',
                'weekly_compliance_rate', 'total_social_media_minutes',
                'total_news_minutes', 'avg_daily_social_media_minutes',
                'avg_daily_news_minutes', 'is_compliant_week'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for stats in weekly_scores.values():
                row = {k: v for k, v in stats.items() if k in fieldnames}
                writer.writerow(row)

        # JSON output
        with open(weekly_json_path, 'w', encoding='utf-8') as f:
            json.dump(weekly_scores, f, indent=2)

    return {
        'daily_csv': str(daily_csv_path),
        'daily_json': str(daily_json_path),
        'weekly_csv': str(weekly_csv_path),
        'weekly_json': str(weekly_json_path)
    }


def run_aggregation(
    input_path: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    rules_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Main pipeline function to run compliance aggregation.

    Args:
        input_path: Path to input compliance logs CSV (optional, uses default)
        output_dir: Output directory for results (optional, uses default)
        rules_config: Custom rules configuration (optional)

    Returns:
        Dictionary containing results and output paths
    """
    if input_path is None:
        input_path = get_path('compliance_logs')

    # Parse logs
    print(f"Reading logs from: {input_path}")
    parsed_logs = parse_csv_logs(input_path)
    print(f"Parsed {len(parsed_logs)} log entries")

    # Validate and normalize
    validated_logs = validate_and_normalize(parsed_logs)
    print(f"Validated {len(validated_logs)} entries")

    # Calculate scores
    daily_scores = calculate_daily_scores(validated_logs, rules_config)
    weekly_scores = calculate_weekly_scores(daily_scores)

    # Write results
    output_files = write_aggregation_results(daily_scores, weekly_scores, output_dir)

    # Summary statistics
    total_participants = len(set(d['participant_id'] for d in daily_scores.values()))
    avg_daily_rate = sum(d['compliance_rate'] for d in daily_scores.values()) / len(daily_scores) if daily_scores else 0.0
    avg_weekly_rate = sum(w['weekly_compliance_rate'] for w in weekly_scores.values()) / len(weekly_scores) if weekly_scores else 0.0

    summary = {
        'total_entries_processed': len(validated_logs),
        'total_participants': total_participants,
        'total_days_logged': len(daily_scores),
        'total_weeks_logged': len(weekly_scores),
        'average_daily_compliance_rate': round(avg_daily_rate, 4),
        'average_weekly_compliance_rate': round(avg_weekly_rate, 4),
        'output_files': output_files
    }

    print(f"\nAggregation complete:")
    print(f"  Participants: {total_participants}")
    print(f"  Daily logs: {len(daily_scores)}")
    print(f"  Weekly aggregates: {len(weekly_scores)}")
    print(f"  Avg daily compliance: {avg_daily_rate:.2%}")
    print(f"  Avg weekly compliance: {avg_weekly_rate:.2%}")
    print(f"  Output written to: {output_dir}")

    return {
        'daily_scores': daily_scores,
        'weekly_scores': weekly_scores,
        'summary': summary,
        'output_files': output_files
    }


def main():
    """Entry point for command-line execution."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Aggregate compliance logs into daily/weekly scores'
    )
    parser.add_argument(
        '--input', '-i',
        type=str,
        default=None,
        help='Path to input compliance logs CSV'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        default=None,
        help='Output directory for results'
    )
    parser.add_argument(
        '--seed', '-s',
        type=int,
        default=None,
        help='Random seed for reproducibility'
    )

    args = parser.parse_args()

    if args.seed is not None:
        set_global_seed(args.seed)

    input_path = Path(args.input) if args.input else None
    output_path = Path(args.output) if args.output else None

    results = run_aggregation(
        input_path=input_path,
        output_dir=output_path
    )

    # Write summary
    summary_path = Path(results['output_files']['daily_json']).parent / 'aggregation_summary.json'
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(results['summary'], f, indent=2)

    print(f"Summary written to: {summary_path}")
    return results


if __name__ == '__main__':
    main()