import logging
import sys
from pathlib import Path
from typing import Optional
import pandas as pd
from config import get_config, ensure_directories_exist
from utils.logger import get_logger

def load_pair_metrics(input_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load pair-level metrics from the derived parquet file.
    Expected schema: project_id, pair_id, response_time_variance, mean_delay, pair_count
    """
    config = get_config()
    if input_path is None:
        input_path = config.get("pair_metrics_path", "data/derived/pair_metrics.parquet")
    
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Pair metrics file not found at {path}")
    
    logger = get_logger("persist_project_metrics")
    logger.info(f"Loading pair metrics from {path}")
    
    df = pd.read_parquet(path)
    
    required_cols = ["project_id", "pair_id", "response_time_variance", "mean_delay", "pair_count"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in pair metrics: {missing}")
    
    logger.info(f"Loaded {len(df)} pair records")
    return df

def aggregate_to_project_level(pair_metrics: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate pair-level metrics to project-level metrics.
    
    Logic (per FR-010):
    1. Calculate median of `response_time_variance` for all pairs in a project.
    2. Calculate mean of `mean_delay` for all pairs in a project (or median if preferred, but mean is standard for delay).
    3. Calculate `team_size` as the number of unique contributors in the project. 
       Since we only have pairs, we estimate team_size as: sqrt(pair_count * 2) is an approximation, 
       but better: count unique authors if available. 
       However, the schema from T012 only has `pair_id`. 
       We will estimate team_size based on the number of unique pairs: 
       If N contributors, max pairs = N*(N-1)/2. 
       We can solve for N roughly, or just use the count of unique pairs as a proxy if exact count is unavailable.
       To be precise, we need the raw event data to count unique authors per project. 
       However, T015 description says: "Schema: project_id, median_variance, mean_delay, team_size, project_age".
       Since T012 output doesn't explicitly list unique authors per project, we must derive team_size from the pair data 
       or assume it was calculated in T012 and passed through. 
       
       Let's assume the `pair_metrics` DataFrame has a way to identify unique contributors or we count unique pairs.
       Actually, a safer bet for `team_size` without raw events is to count the number of unique `pair_id`s 
       and map that to an estimated team size, OR if the `pair_id` encodes the authors, we can count unique authors.
       
       Given the constraints and typical data flow:
       If `pair_id` is a string like "A_B", we can split and count unique authors.
       If `pair_id` is an integer ID, we can't easily recover authors without a mapping.
       
       Alternative: The task T015 description implies we just need to aggregate. 
       Let's assume we calculate `team_size` as the number of unique pairs + 1? No.
       Let's look at T012 output schema: `project_id`, `pair_id`, `response_time_variance`, `mean_delay`, `pair_count`.
       `pair_count` might be the number of interactions for that pair.
       
       To get `team_size` accurately, we ideally need the raw event data to count unique `author_id`s per project.
       Since T015 depends on T014 (which filters projects), and T014 depends on T012, 
       and T012 calculates metrics, we might need to load the raw events or a derived file with unique authors.
       
       However, if we strictly follow the task: "Calculate median of response_time_variance for all pairs in a project".
       For `team_size`, if we cannot get it from the pair metrics directly, we might need to load the raw events 
       to count unique authors per project.
       
       Let's implement a fallback:
       1. Try to infer team_size from pair_id if it's a string representation of authors.
       2. If not, we might need to load the raw events (data/raw/events.json) to count unique authors.
       
       Given the pipeline flow, loading raw events here is acceptable if needed for accurate team_size.
       But the task says "Input: pair_metrics".
       
       Let's assume the `pair_id` format is "author1_id_author2_id" or similar, allowing us to extract unique authors.
       If `pair_id` is just an index, we can't.
       
       Let's try to count unique authors from `pair_id` assuming it's a string like "123_456".
       If that fails, we will estimate team_size = number of unique pairs + 1 (very rough) or just skip and set to -1?
       No, we must provide a value.
       
       Better approach: The `pair_metrics` table should ideally have been generated with enough info.
       Let's assume we can reconstruct the set of authors for each project from the `pair_id` column.
       We'll parse `pair_id` assuming it's "id1_id2".
       
       If `pair_id` is not parseable, we will count unique pairs and estimate team_size = int(sqrt(2 * num_pairs)) + 1?
       No, that's too approximate.
       
       Let's check the T012 implementation (which we don't see, but we know it exists).
       If T012 didn't output unique authors, we have to load raw events.
       
       Decision: To be robust, we will load the raw events file if available to count unique authors per project.
       This ensures `team_size` is accurate.
       
       Also for `project_age`: We need the first and last event timestamp per project from raw events.
       
       So, `aggregate_to_project_level` will:
       1. Load raw events (if available) to calculate `team_size` and `project_age`.
       2. Aggregate `response_time_variance` (median) and `mean_delay` (mean) from `pair_metrics`.
    """
    config = get_config()
    raw_events_path = config.get("raw_events_path", "data/raw/events.json")
    
    logger = get_logger("persist_project_metrics")
    
    # Aggregate metrics from pair_metrics
    project_metrics = pair_metrics.groupby("project_id").agg(
        median_variance=("response_time_variance", "median"),
        mean_delay=("mean_delay", "mean")
    ).reset_index()
    
    # Calculate team_size and project_age from raw events
    try:
        raw_df = pd.read_json(raw_events_path, lines=True)
        # Ensure timestamp is datetime
        if "timestamp" in raw_df.columns:
            raw_df["timestamp"] = pd.to_datetime(raw_df["timestamp"], errors="coerce")
        else:
            # Try created_at if timestamp is missing
            if "created_at" in raw_df.columns:
                raw_df["timestamp"] = pd.to_datetime(raw_df["created_at"], errors="coerce")
            else:
                raise ValueError("No timestamp column found in raw events")
        
        # Calculate team_size (unique authors) per project
        team_sizes = raw_df.groupby("project_id")["author_id"].nunique().reset_index()
        team_sizes.columns = ["project_id", "team_size"]
        
        # Calculate project_age (days between first and last event)
        project_age = raw_df.groupby("project_id")["timestamp"].agg(["min", "max"]).reset_index()
        project_age["project_age"] = (project_age["max"] - project_age["min"]).dt.days
        project_age = project_age[["project_id", "project_age"]]
        
        # Merge
        project_metrics = project_metrics.merge(team_sizes, on="project_id", how="left")
        project_metrics = project_metrics.merge(project_age, on="project_id", how="left")
        
    except FileNotFoundError:
        logger.warning(f"Raw events file not found at {raw_events_path}. Cannot calculate team_size and project_age accurately.")
        project_metrics["team_size"] = -1
        project_metrics["project_age"] = -1
    except Exception as e:
        logger.warning(f"Error processing raw events for team_size/age: {e}. Setting defaults.")
        project_metrics["team_size"] = -1
        project_metrics["project_age"] = -1
    
    logger.info(f"Aggregated {len(project_metrics)} project-level metrics")
    return project_metrics

def run_aggregation_pipeline(input_path: Optional[str] = None, output_path: Optional[str] = None) -> pd.DataFrame:
    """
    Main pipeline function to load pair metrics, aggregate to project level, and persist.
    """
    config = get_config()
    ensure_directories_exist(config)
    
    if input_path is None:
        input_path = config.get("pair_metrics_path", "data/derived/pair_metrics.parquet")
    if output_path is None:
        output_path = config.get("project_metrics_path", "data/derived/project_metrics.csv")
    
    logger = get_logger("persist_project_metrics")
    logger.info("Starting project metrics aggregation pipeline")
    
    # Load
    pair_metrics = load_pair_metrics(input_path)
    
    # Aggregate
    project_metrics = aggregate_to_project_level(pair_metrics)
    
    # Persist
    output_file = Path(output_path)
    project_metrics.to_csv(output_file, index=False)
    logger.info(f"Project metrics saved to {output_file}")
    
    return project_metrics

def main():
    """
    Entry point for running the aggregation pipeline.
    """
    logging.basicConfig(level=logging.INFO)
    run_aggregation_pipeline()

if __name__ == "__main__":
    main()