import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
DATA_DIR = Path("data/processed")
FIGURES_DIR = Path("figures")
REPORTS_DIR = Path("docs")

# Ensure directories exist
FIGURES_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

def load_dependencies_data(csv_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load dependencies data from CSV file.
    
    Args:
        csv_path: Path to the CSV file. If None, uses default path.
        
    Returns:
        DataFrame with dependencies data
    """
    if csv_path is None:
        csv_path = DATA_DIR / "dependencies_raw.csv"
    
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Dependencies data not found at {csv_path}")
    
    logger.info(f"Loading dependencies data from {csv_path}")
    df = pd.read_csv(csv_path)
    
    # Ensure necessary columns exist
    required_cols = ['category', 'is_unmaintained', 'age_in_days', 'vulnerability_count']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in data: {missing_cols}")
    
    return df

def calculate_unmaintained_proportions_by_category(df: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate the proportion of unmaintained dependencies for each category.
    
    Args:
        df: DataFrame with dependencies data
        
    Returns:
        Dictionary mapping category to unmaintained proportion
    """
    if 'is_unmaintained' not in df.columns or 'category' not in df.columns:
        raise ValueError("DataFrame must contain 'is_unmaintained' and 'category' columns")
    
    # Group by category and calculate proportions
    category_stats = df.groupby('category').agg(
        total=('is_unmaintained', 'count'),
        unmaintained_count=('is_unmaintained', 'sum')
    ).reset_index()
    
    category_stats['unmaintained_proportion'] = category_stats['unmaintained_count'] / category_stats['total']
    
    result = dict(zip(category_stats['category'], category_stats['unmaintained_proportion']))
    logger.info(f"Calculated unmaintained proportions for {len(result)} categories")
    return result

def generate_histogram_by_category(df: pd.DataFrame, output_path: Optional[str] = None) -> str:
    """
    Generate a histogram of unmaintained dependency percentages by category.
    
    Args:
        df: DataFrame with dependencies data
        output_path: Path to save the histogram image. If None, uses default path.
        
    Returns:
        Path to the generated histogram file
    """
    if output_path is None:
        output_path = FIGURES_DIR / "unmaintained_histogram_by_category.png"
    else:
        output_path = Path(output_path)
    
    logger.info(f"Generating histogram for unmaintained dependencies by category")
    
    # Calculate unmaintained proportions by category
    proportions = calculate_unmaintained_proportions_by_category(df)
    
    # Sort categories by proportion for better visualization
    sorted_categories = sorted(proportions.items(), key=lambda x: x[1], reverse=True)
    categories = [cat for cat, _ in sorted_categories]
    values = [prop for _, prop in sorted_categories]
    
    # Create the histogram
    plt.figure(figsize=(12, 8))
    bars = plt.bar(categories, values, color='skyblue', edgecolor='black', alpha=0.8)
    
    # Add value labels on bars
    for bar, value in zip(bars, values):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{value:.2%}',
                ha='center', va='bottom', fontsize=9)
    
    plt.title('Distribution of Unmaintained Dependencies by Category', fontsize=14, fontweight='bold')
    plt.xlabel('Category', fontsize=12)
    plt.ylabel('Proportion of Unmaintained Dependencies', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.ylim(0, max(values) * 1.1 if values else 1)
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    
    # Save the figure
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Histogram saved to {output_path}")
    return str(output_path)

def generate_category_distribution_plot(df: pd.DataFrame, output_path: Optional[str] = None) -> str:
    """
    Generate a plot showing the distribution of packages across categories.
    
    Args:
        df: DataFrame with dependencies data
        output_path: Path to save the plot image. If None, uses default path.
        
    Returns:
        Path to the generated plot file
    """
    if output_path is None:
        output_path = FIGURES_DIR / "category_distribution.png"
    else:
        output_path = Path(output_path)
    
    logger.info(f"Generating category distribution plot")
    
    # Count packages per category
    category_counts = df['category'].value_counts().reset_index()
    category_counts.columns = ['category', 'count']
    
    # Sort by count
    category_counts = category_counts.sort_values('count', ascending=True)
    
    # Create the plot
    plt.figure(figsize=(12, 8))
    bars = plt.barh(category_counts['category'], category_counts['count'], color='lightgreen', edgecolor='black', alpha=0.8)
    
    # Add value labels on bars
    for bar, count in zip(bars, category_counts['count']):
        width = bar.get_width()
        plt.text(width + 0.5, bar.get_y() + bar.get_height()/2,
                f'{int(count)}',
                ha='left', va='center', fontsize=9)
    
    plt.title('Distribution of Packages by Category', fontsize=14, fontweight='bold')
    plt.xlabel('Number of Packages', fontsize=12)
    plt.ylabel('Category', fontsize=12)
    plt.tight_layout()
    
    # Save the figure
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Category distribution plot saved to {output_path}")
    return str(output_path)

def create_visualization_summary(df: pd.DataFrame, metrics_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Create all visualizations and generate a summary report.
    
    Args:
        df: DataFrame with dependencies data
        metrics_path: Path to save metrics JSON. If None, uses default path.
        
    Returns:
        Dictionary containing paths to generated files and summary metrics
    """
    if metrics_path is None:
        metrics_path = DATA_DIR / "visualization_metrics.json"
    else:
        metrics_path = Path(metrics_path)
    
    logger.info("Creating visualization summary")
    
    # Generate histogram
    histogram_path = generate_histogram_by_category(df)
    
    # Generate category distribution plot
    distribution_path = generate_category_distribution_plot(df)
    
    # Calculate summary metrics
    proportions = calculate_unmaintained_proportions_by_category(df)
    total_categories = len(proportions)
    avg_proportion = sum(proportions.values()) / len(proportions) if proportions else 0
    max_proportion = max(proportions.values()) if proportions else 0
    min_proportion = min(proportions.values()) if proportions else 0
    
    summary = {
        "histogram_path": histogram_path,
        "distribution_path": distribution_path,
        "total_categories": total_categories,
        "average_unmaintained_proportion": avg_proportion,
        "max_unmaintained_proportion": max_proportion,
        "min_unmaintained_proportion": min_proportion,
        "category_proportions": proportions,
        "generated_at": pd.Timestamp.now().isoformat()
    }
    
    # Save metrics
    with open(metrics_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Visualization summary saved to {metrics_path}")
    return summary

def main():
    """
    Main function to run the visualization generation for unmaintained dependencies.
    This function loads the processed data, generates histograms and distribution plots,
    and saves a summary report.
    """
    try:
        # Load data
        df = load_dependencies_data()
        
        # Create visualizations and summary
        summary = create_visualization_summary(df)
        
        print(f"✓ Histogram generated: {summary['histogram_path']}")
        print(f"✓ Distribution plot generated: {summary['distribution_path']}")
        print(f"✓ Metrics saved: {DATA_DIR / 'visualization_metrics.json'}")
        print(f"✓ Total categories analyzed: {summary['total_categories']}")
        print(f"✓ Average unmaintained proportion: {summary['average_unmaintained_proportion']:.2%}")
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during visualization generation: {e}")
        return 1

if __name__ == "__main__":
    exit(main())