import pandas as pd
import numpy as np
from typing import Tuple, Optional, Dict, Any
from pathlib import Path
from data_models import TeamMetrics, create_team_metrics_dataframe
from utils.logging import get_logger, log_info, log_warning, log_error

logger = get_logger(__name__)

def calculate_traditional_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate traditional metrics (AVG, ERA) per game.
    Assumes df has columns: ['team', 'hits', 'at_bats', 'earned_runs', 'innings_pitched', 'year']
    """
    logger.info("Calculating traditional metrics (AVG, ERA)...")
    df = df.copy()
    
    # Batting Average (AVG) = Hits / At Bats
    df['avg'] = df['hits'] / df['at_bats'].replace(0, np.nan)
    
    # Earned Run Average (ERA) = (Earned Runs * 9) / Innings Pitched
    df['era'] = (df['earned_runs'] * 9) / df['innings_pitched'].replace(0, np.nan)
    
    return df

def calculate_advanced_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate advanced metrics (wOBA, BABIP, park-adjusted run expectancy) per game.
    Assumes df has columns: ['team', 'singles', 'doubles', 'triples', 'homeruns', 
                             'walks', 'hit_by_pitch', 'plate_appearances', 'outs', 
                             'park_factor', 'year']
    """
    logger.info("Calculating advanced metrics (wOBA, BABIP, park-adjusted RE)...")
    df = df.copy()
    
    # wOBA weights (approximate 2018-2022 MLB averages)
    woba_weights = {
        'bb': 0.69, 'hbp': 0.72, '1b': 0.89, '2b': 1.27, '3b': 1.62, 'hr': 2.10
    }
    
    # Calculate wOBA numerator
    woba_num = (
        df.get('walks', 0) * woba_weights['bb'] +
        df.get('hit_by_pitch', 0) * woba_weights['hbp'] +
        df.get('singles', 0) * woba_weights['1b'] +
        df.get('doubles', 0) * woba_weights['2b'] +
        df.get('triples', 0) * woba_weights['3b'] +
        df.get('homeruns', 0) * woba_weights['hr']
    )
    
    # wOBA denominator: Plate Appearances - IBB - SF
    # Assuming IBB and SF are not in df for simplicity, using PA
    woba_denom = df.get('plate_appearances', 1).replace(0, np.nan)
    df['woba'] = woba_num / woba_denom
    
    # BABIP = (Hits - Homeruns) / (At Bats - Homeruns - Strikeouts + Sacrifice Flies)
    hits = df.get('singles', 0) + df.get('doubles', 0) + df.get('triples', 0) + df.get('homeruns', 0)
    at_bats = df.get('at_bats', 1)
    strikeouts = df.get('strikeouts', 0)
    sf = df.get('sacrifice_flies', 0)
    
    babip_denom = at_bats - df.get('homeruns', 0) - strikeouts + sf
    df['babip'] = (hits - df.get('homeruns', 0)) / babip_denom.replace(0, np.nan)
    
    # Park-adjusted Run Expectancy (simplified: RE * park_factor)
    # Assuming 'run_expectancy' is a raw metric calculated elsewhere or approximated
    if 'run_expectancy' in df.columns:
        df['park_adj_re'] = df['run_expectancy'] * df.get('park_factor', 1.0)
    else:
        # Fallback: use runs scored as proxy
        df['park_adj_re'] = df.get('runs_scored', 0) * df.get('park_factor', 1.0)
        
    return df

def handle_missing_advanced_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handle missing advanced metrics by imputing with league average for that year.
    """
    logger.info("Handling missing advanced metrics via league average imputation...")
    df = df.copy()
    
    advanced_cols = ['woba', 'babip', 'park_adj_re']
    for col in advanced_cols:
        if col in df.columns:
            # Group by year to get league average
            league_avg = df.groupby('year')[col].transform('mean')
            df[col] = df[col].fillna(league_avg)
            missing_count = df[col].isna().sum()
            if missing_count > 0:
                log_warning(f"Still {missing_count} missing values for {col} after imputation")
                
    return df

def apply_temporal_split(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split data into Train (<=2018) and Test (2019-2022).
    Exclude 2020 pandemic season.
    
    Args:
        df: DataFrame with a 'year' column.
        
    Returns:
        Tuple of (train_df, test_df)
    """
    logger.info("Applying temporal split: Train (<=2018), Test (2019-2022), excluding 2020...")
    df = df.copy()
    
    # Ensure 'year' is integer
    if not pd.api.types.is_integer_dtype(df['year']):
        df['year'] = df['year'].astype(int)
    
    # Filter out 2020
    df_no_2020 = df[df['year'] != 2020]
    log_info(f"Excluded {len(df) - len(df_no_2020)} rows from year 2020 (pandemic season).")
    
    # Train: year <= 2018
    train_df = df_no_2020[df_no_2020['year'] <= 2018].copy()
    
    # Test: 2019 <= year <= 2022
    test_df = df_no_2020[(df_no_2020['year'] >= 2019) & (df_no_2020['year'] <= 2022)].copy()
    
    log_info(f"Train set size: {len(train_df)} (Years: {train_df['year'].min()}-{train_df['year'].max()})")
    log_info(f"Test set size: {len(test_df)} (Years: {test_df['year'].min()}-{test_df['year'].max()})")
    
    # Verify no leakage
    max_train_year = train_df['year'].max()
    min_test_year = test_df['year'].min() if not test_df.empty else 9999
    
    if min_test_year <= max_train_year:
        log_error(f"Leakage detected! Max train year: {max_train_year}, Min test year: {min_test_year}")
        raise ValueError("Temporal split failed: Data leakage detected between train and test sets.")
        
    return train_df, test_df

def engineer_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Main pipeline function to engineer features and split data.
    
    1. Calculate Traditional Metrics
    2. Calculate Advanced Metrics
    3. Handle Missing Advanced Metrics
    4. Apply Temporal Split
    
    Args:
        df: Raw DataFrame from data_loader.
        
    Returns:
        Tuple of (train_features, test_features)
    """
    logger.info("Starting full feature engineering pipeline...")
    
    # 1. Traditional Metrics
    df = calculate_traditional_metrics(df)
    
    # 2. Advanced Metrics
    df = calculate_advanced_metrics(df)
    
    # 3. Handle Missing Advanced Metrics
    df = handle_missing_advanced_metrics(df)
    
    # 4. Temporal Split
    train_df, test_df = apply_temporal_split(df)
    
    return train_df, test_df

def main():
    """
    Entry point for feature engineering script.
    Expects a raw CSV in data/raw/processed_games.csv (or similar path defined in config).
    Outputs: data/processed/train_features.csv, data/processed/test_features.csv
    """
    from config import ensure_directories
    import json
    
    # Ensure directories exist
    ensure_directories()
    
    # Load raw data
    # Assuming the output from T012a is at this path. 
    # In a real scenario, this path might be read from config or passed as arg.
    input_path = Path("data/processed/processed_games.csv")
    
    if not input_path.exists():
        # Fallback for testing if the specific file doesn't exist yet, 
        # but T012a should have created it.
        log_error(f"Input file not found: {input_path}. Ensure T012a has run.")
        return
        
    log_info(f"Loading raw data from {input_path}")
    df = pd.read_csv(input_path)
    
    # Run engineering
    train_df, test_df = engineer_features(df)
    
    # Save outputs
    train_path = Path("data/processed/train_features.csv")
    test_path = Path("data/processed/test_features.csv")
    
    train_df.to_csv(train_path, index=False)
    test_df.to_csv(test_path, index=False)
    
    log_info(f"Saved train features to {train_path}")
    log_info(f"Saved test features to {test_path}")
    
    # Log summary stats
    print(json.dumps({
        "train_rows": len(train_df),
        "test_rows": len(test_df),
        "train_years": f"{train_df['year'].min()}-{train_df['year'].max()}",
        "test_years": f"{test_df['year'].min()}-{test_df['year'].max()}"
    }, indent=2))

if __name__ == "__main__":
    main()