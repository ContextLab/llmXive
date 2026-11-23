import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from scipy.stats import pearsonr, spearmanr

from utils.logger import setup_logger, AnalysisError
from config import get_data_dir, get_output_dir

# Configure logging
logger = setup_logger(__name__)

class IndependenceCheck:
    """
    Checks for circularity between static keyword extraction scores (used for filtering)
    and the experimental strategies (TF-IDF, etc.).
    
    If correlation >= 0.3, the run MUST fail with "Circularity Detected" error.
    """

    def __init__(self, filtered_data_path: str, strategies: List[str]):
        """
        Args:
            filtered_data_path: Path to the filtered dataset (e.g., data/filtered_swe_bench_v1.parquet)
            strategies: List of strategy names to check against (e.g., ['tfidf', 'diff_aware', 'semantic_summarization'])
        """
        self.filtered_data_path = Path(filtered_data_path)
        self.strategies = strategies
        self.correlation_threshold = 0.3
        self.results: Dict[str, float] = {}

    def load_filtered_data(self) -> pd.DataFrame:
        """
        Loads the filtered dataset.
        Expects columns: 'instance_id', 'static_keyword_score' (or similar), 
        and potentially strategy-specific scores if pre-calculated.
        
        If strategy scores are not present, we simulate the check based on 
        the assumption that the filtering logic (static keywords) is the 
        independent variable and the strategy retrieval scores are the dependent.
        
        Note: In a real execution, the dataset would contain the scores 
        calculated during the filtering/processing phase.
        """
        if not self.filtered_data_path.exists():
            raise FileNotFoundError(f"Filtered data file not found: {self.filtered_data_path}")
        
        logger.info(f"Loading filtered data from {self.filtered_data_path}")
        
        # Determine file type based on extension
        suffix = self.filtered_data_path.suffix.lower()
        if suffix == '.parquet':
            df = pd.read_parquet(self.filtered_data_path)
        elif suffix == '.csv':
            df = pd.read_csv(self.filtered_data_path)
        elif suffix == '.jsonl':
            df = pd.read_json(self.filtered_data_path, lines=True)
        else:
            raise ValueError(f"Unsupported file format: {suffix}")
        
        # Verify required columns exist
        # We expect a 'static_keyword_score' or similar column used for filtering
        # We also expect columns representing the strategy scores (e.g., 'tfidf_score', 'diff_score')
        # If these are not present, we cannot calculate the correlation directly.
        # However, the task description implies we need to check the correlation 
        # between the *static keyword extraction scores* (used for filtering) 
        # and the *experimental strategies* (TF-IDF, etc.).
        
        # Assumption: The filtered dataset contains a column 'static_keyword_score'
        # and potentially 'strategy_{name}_score' or we need to load strategy scores from elsewhere.
        # For this implementation, we assume the filtered dataset contains:
        # - 'static_keyword_score': The score used to filter the instances.
        # - 'strategy_scores': A dictionary or JSON string containing scores per strategy.
        # OR
        # - Columns named 'tfidf_score', 'diff_aware_score', etc.
        
        required_cols = ['static_keyword_score']
        missing_cols = [c for c in required_cols if c not in df.columns]
        
        if missing_cols:
            # Try to find alternative names
            possible_alt_names = {
                'static_keyword_score': ['static_score', 'keyword_score', 'filter_score']
            }
            for alt in possible_alt_names.get('static_keyword_score', []):
                if alt in df.columns:
                    df = df.rename(columns={alt: 'static_keyword_score'})
                    missing_cols.remove('static_keyword_score')
                    break
            
            if missing_cols:
                raise ValueError(f"Missing required column(s) for independence check: {missing_cols}. "
                               f"Available columns: {df.columns.tolist()}")

        # Check for strategy score columns
        strategy_cols = []
        for strategy in self.strategies:
            # Look for columns like 'tfidf_score', 'diff_aware_score', etc.
            col_name = f"{strategy}_score"
            if col_name in df.columns:
                strategy_cols.append(col_name)
            else:
                # Try to find a column that might contain strategy scores as a JSON object
                # or a generic 'strategy_score' column
                pass 
        
        # If specific strategy columns are not found, we might need to infer or load them.
        # However, for the purpose of this check, we will assume the data contains 
        # the necessary scores. If not, we raise an error.
        if not strategy_cols:
            # Attempt to load from a separate file if available, or raise error
            logger.warning("No specific strategy score columns found. "
                         "Attempting to load from a separate strategy_scores file if available.")
            # This is a simplified check; in a full implementation, we might load scores from a separate source.
            # For now, we will assume the data is present or raise an error.
            raise ValueError("Could not find strategy score columns. "
                           f"Expected columns like: {[f'{s}_score' for s in self.strategies]}")

        return df, strategy_cols

    def calculate_correlation(self, df: pd.DataFrame, strategy_cols: List[str]) -> Dict[str, float]:
        """
        Calculates the Pearson correlation coefficient between 'static_keyword_score' 
        and each strategy score column.
        """
        correlations = {}
        static_col = 'static_keyword_score'
        
        for strategy_col in strategy_cols:
            # Drop rows with NaN in either column
            valid_data = df[[static_col, strategy_col]].dropna()
            
            if len(valid_data) < 2:
                logger.warning(f"Insufficient data for correlation calculation between {static_col} and {strategy_col}")
                correlations[strategy_col] = np.nan
                continue
            
            # Calculate Pearson correlation
            corr, p_value = pearsonr(valid_data[static_col], valid_data[strategy_col])
            correlations[strategy_col] = corr
            
            logger.info(f"Correlation between {static_col} and {strategy_col}: {corr:.4f} (p={p_value:.4f})")
            
            # Also calculate Spearman rank correlation as a robustness check
            spearman_corr, spearman_p = spearmanr(valid_data[static_col], valid_data[strategy_col])
            logger.info(f"Spearman correlation between {static_col} and {strategy_col}: {spearman_corr:.4f} (p={spearman_p:.4f})")

        return correlations

    def check_circularity(self) -> bool:
        """
        Checks if any correlation exceeds the threshold.
        Returns True if circularity is detected (correlation >= threshold).
        """
        df, strategy_cols = self.load_filtered_data()
        self.results = self.calculate_correlation(df, strategy_cols)
        
        max_corr = 0.0
        max_corr_strategy = None
        
        for strategy, corr in self.results.items():
            if not np.isnan(corr):
                abs_corr = abs(corr)
                if abs_corr > max_corr:
                    max_corr = abs_corr
                    max_corr_strategy = strategy
        
        logger.info(f"Maximum absolute correlation detected: {max_corr:.4f} for strategy {max_corr_strategy}")
        
        if max_corr >= self.correlation_threshold:
            logger.error(f"Circularity Detected: Correlation ({max_corr:.4f}) exceeds threshold ({self.correlation_threshold}) "
                       f"for strategy {max_corr_strategy}.")
            return True
        
        logger.info("Independence check passed. No significant circularity detected.")
        return False

    def save_results(self, output_path: Optional[Path] = None):
        """
        Saves the correlation results to a JSON file.
        """
        if output_path is None:
            output_dir = get_output_dir()
            output_path = Path(output_dir) / "construct_validity_results.json"
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        results_data = {
            "threshold": self.correlation_threshold,
            "max_correlation": max([abs(v) for v in self.results.values() if not np.isnan(v)]),
            "correlations": {k: float(v) if not np.isnan(v) else None for k, v in self.results.items()}
        }
        
        with open(output_path, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        logger.info(f"Results saved to {output_path}")


def main():
    """
    Main entry point for the IndependenceCheck script.
    """
    parser = argparse.ArgumentParser(description="Check for circularity between filtering criteria and experimental strategies.")
    parser.add_argument("--input", type=str, required=True, help="Path to the filtered dataset (e.g., data/filtered_swe_bench_v1.parquet)")
    parser.add_argument("--strategies", type=str, nargs="+", default=["tfidf", "diff_aware", "semantic_summarization"], 
                      help="List of strategies to check against")
    parser.add_argument("--output", type=str, help="Path to save results JSON (optional)")
    args = parser.parse_args()

    try:
        checker = IndependenceCheck(args.input, args.strategies)
        is_circular = checker.check_circularity()
        
        if args.output:
            checker.save_results(Path(args.output))
        else:
            checker.save_results()

        if is_circular:
            logger.error("FATAL: Circularity detected. The run must be aborted.")
            sys.exit(1)
        
        logger.info("IndependenceCheck completed successfully.")
        sys.exit(0)

    except Exception as e:
        logger.error(f"IndependenceCheck failed with error: {e}", exc_info=True)
        raise AnalysisError(f"IndependenceCheck failed: {e}") from e


if __name__ == "__main__":
    main()