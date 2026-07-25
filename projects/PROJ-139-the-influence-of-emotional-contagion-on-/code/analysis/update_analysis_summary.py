"""
T048: Ensure the docs/analysis_summary.md includes a section on Data Coverage.

This script reads data/processed/all_threads_classified.csv to calculate:
1. Percentage of threads from each subreddit/site.
2. Distribution of thread lengths (reply counts).

It then appends this section to docs/analysis_summary.md.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_classified_threads() -> pd.DataFrame:
    """Load the classified threads dataset."""
    path = Path("data/processed/all_threads_classified.csv")
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    
    logger.info(f"Loading classified threads from {path}")
    df = pd.read_csv(path)
    
    # Validate expected columns
    required_cols = ['thread_id', 'subreddit_or_site', 'reply_count']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in {path}: {missing_cols}")
    
    return df

def calculate_data_coverage_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate distribution statistics for data coverage."""
    stats = {}
    
    # 1. Percentage of threads from each subreddit/site
    total_threads = len(df)
    if total_threads == 0:
        logger.warning("Dataset is empty. Cannot calculate coverage percentages.")
        stats['subreddit_distribution'] = []
    else:
        subreddit_counts = df['subreddit_or_site'].value_counts()
        stats['subreddit_distribution'] = [
            {
                'source': str(source),
                'count': int(count),
                'percentage': round((count / total_threads) * 100, 2)
            }
            for source, count in subreddit_counts.items()
        ]
        # Sort by percentage descending
        stats['subreddit_distribution'].sort(key=lambda x: x['percentage'], reverse=True)
    
    # 2. Distribution of thread lengths (reply counts)
    if 'reply_count' in df.columns:
        reply_counts = df['reply_count']
        stats['thread_length_distribution'] = {
            'total_threads': int(total_threads),
            'mean_reply_count': round(float(reply_counts.mean()), 2) if not reply_counts.empty else 0.0,
            'median_reply_count': round(float(reply_counts.median()), 2) if not reply_counts.empty else 0.0,
            'min_reply_count': int(reply_counts.min()) if not reply_counts.empty else 0,
            'max_reply_count': int(reply_counts.max()) if not reply_counts.empty else 0,
            'std_reply_count': round(float(reply_counts.std()), 2) if not reply_counts.empty else 0.0
        }
        
        # Bin distribution for better readability (0-5, 6-10, 11-20, 21+)
        bins = [0, 5, 10, 20, 1000] # 1000 acts as infinity for max
        labels = ['0-5', '6-10', '11-20', '21+']
        df['reply_bin'] = pd.cut(reply_counts, bins=bins, labels=labels, right=True)
        bin_counts = df['reply_bin'].value_counts().sort_index()
        
        stats['thread_length_bins'] = [
            {
                'range': str(label),
                'count': int(count),
                'percentage': round((count / total_threads) * 100, 2)
            }
            for label, count in bin_counts.items()
            if pd.notna(label)
        ]
    else:
        stats['thread_length_distribution'] = None
        stats['thread_length_bins'] = None
    
    return stats

def generate_data_coverage_section(stats: Dict[str, Any]) -> str:
    """Generate the markdown content for the Data Coverage section."""
    lines = [
        "\n---",
        "## Data Coverage",
        "---\n"
    ]
    
    # Subreddit/Site Distribution
    lines.append("### Source Distribution")
    if stats.get('subreddit_distribution'):
        lines.append("The dataset is composed of the following sources:")
        lines.append("")
        lines.append("| Source | Thread Count | Percentage |")
        lines.append("| :--- | :--- | :--- |")
        for item in stats['subreddit_distribution']:
            lines.append(f"| {item['source']} | {item['count']} | {item['percentage']}% |")
        lines.append("")
    else:
        lines.append("No source distribution data available.")
        lines.append("")
    
    # Thread Length Distribution
    lines.append("### Thread Length Distribution")
    if stats.get('thread_length_distribution'):
        dist = stats['thread_length_distribution']
        lines.append(f"- **Total Threads**: {dist['total_threads']}")
        lines.append(f"- **Mean Reply Count**: {dist['mean_reply_count']}")
        lines.append(f"- **Median Reply Count**: {dist['median_reply_count']}")
        lines.append(f"- **Range**: {dist['min_reply_count']} to {dist['max_reply_count']}")
        lines.append(f"- **Standard Deviation**: {dist['std_reply_count']}")
        lines.append("")
        
        if stats.get('thread_length_bins'):
            lines.append("### Reply Count Bins")
            lines.append("")
            lines.append("| Reply Range | Thread Count | Percentage |")
            lines.append("| :--- | :--- | :--- |")
            for item in stats['thread_length_bins']:
                lines.append(f"| {item['range']} | {item['count']} | {item['percentage']}% |")
            lines.append("")
    else:
        lines.append("No thread length distribution data available.")
        lines.append("")
    
    return "\n".join(lines)

def append_to_summary(summary_path: Path, new_content: str):
    """Append the new content to the analysis summary file."""
    if not summary_path.exists():
        logger.warning(f"Summary file not found at {summary_path}. Creating new file.")
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return

    with open(summary_path, 'r', encoding='utf-8') as f:
        existing_content = f.read()
    
    # Check if section already exists to avoid duplication
    if "## Data Coverage" in existing_content:
        logger.info("Data Coverage section already exists. Updating content.")
        # Simple strategy: remove old section and append new
        # Find start of section
        start_idx = existing_content.find("## Data Coverage")
        if start_idx != -1:
            # Find end of section (next section starting with ## or end of file)
            end_idx = existing_content.find("\n## ", start_idx + 1)
            if end_idx == -1:
                end_idx = len(existing_content)
            
            # Reconstruct: everything before section + new content
            new_file_content = existing_content[:start_idx] + new_content
            # If there was content after the old section, append it
            if end_idx < len(existing_content):
                new_file_content += existing_content[end_idx:]
            
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write(new_file_content)
        else:
            # Fallback: just append
            with open(summary_path, 'a', encoding='utf-8') as f:
                f.write(new_content)
    else:
        # Append to end
        with open(summary_path, 'a', encoding='utf-8') as f:
            f.write(new_content)

def main():
    """Main entry point for T048."""
    try:
        # Load data
        df = load_classified_threads()
        
        # Calculate stats
        stats = calculate_data_coverage_stats(df)
        
        # Generate markdown
        section_content = generate_data_coverage_section(stats)
        
        # Determine paths
        project_root = Path(__file__).resolve().parents[2]
        summary_path = project_root / "docs" / "analysis_summary.md"
        
        # Ensure docs directory exists
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Append to file
        append_to_summary(summary_path, section_content)
        
        logger.info(f"Successfully updated {summary_path} with Data Coverage section.")
        
        # Log summary stats for verification
        if stats.get('subreddit_distribution'):
            sources = [s['source'] for s in stats['subreddit_distribution']]
            logger.info(f"Sources found: {sources}")
        
        if stats.get('thread_length_distribution'):
            logger.info(f"Thread length stats: mean={stats['thread_length_distribution']['mean_reply_count']}")
        
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()