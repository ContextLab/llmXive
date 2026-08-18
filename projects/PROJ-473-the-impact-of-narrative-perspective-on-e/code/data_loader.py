import os
import re
import json
import hashlib
import requests
import pandas as pd
import logging

# Importing HuggingFace datasets for real data retrieval
try:
    from datasets import load_dataset
except ImportError:
    raise ImportError(
        "The 'datasets' package is required. "
        "Install it via: pip install datasets"
    )

def fetch_gutenberg_stories(max_stories=10): # Added max stories to limit download
    """Fetches a limited number of stories from Project Gutenberg."""
    base_url = "https://www.gutenberg.org/files/"
    story_ids = [1342, 2701, 69, 84, 1513]  # Example story IDs
    stories = {}

    for story_id in story_ids[:max_stories]:
        try:
            text_url = f"{base_url}{story_id}/{story_id}-0.txt"
            response = requests.get(text_url)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            stories[story_id] = response.text
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching story {story_id}: {e}")

    return stories


def load_reader_response_data(): # Removed URL, using a dummy dataset for demonstration
  """Loads the reader response data.  Returns an empty DataFrame if no valid file is found."""
  try:
      # Attempt to load from a local file (for testing/development)
      df = pd.read_csv("data/raw/moral_judgement_dataset.csv")
      return df

  except FileNotFoundError:
      logging.warning("Reader response dataset not found locally.")
      return pd.DataFrame() # Return an empty DataFrame instead of raising an error



def fetch_moral_foundations_twitter(max_tweets=10):
    """Placeholder for fetching moral foundations data from Twitter."""
    # This is a placeholder as accessing the Twitter API requires authentication and rate limits
    logging.warning("Twitter API access not implemented.")
    return []

def fetch_reader_response_data(output_path="data/processed/reader_response.csv"):
    """
    Fetches a verified external reader-response dataset from HuggingFace.
    Data Source: moral-foundation/twitter (as per spec).
    Schema: The fetched dataset MUST contain columns `story_id`, `empathy_score`, and `moral_judgement_score`.
    
    Logic:
    1. Fetch the dataset from the HuggingFace hub (`moral-foundation/twitter`).
    2. Validate that the dataset contains `story_id`, `empathy_score`, and `moral_judgement_score` columns. 
       If missing, raise a `DataValidationError`.
    3. (Optional) If `text_reflection` exists, include it; otherwise, ignore it.
    4. Output `data/processed/reader_response.csv` with columns `story_id`, `empathy_score`, 
       `moral_judgement_score`, `participant_id`, and `text_reflection` (if present).
    
    Raises:
        DataValidationError: If the required columns are missing in the fetched dataset.
        Exception: If the dataset cannot be fetched.
    """
    dataset_name = "moral-foundation/twitter"
    required_columns = ["story_id", "empathy_score", "moral_judgement_score"]
    
    logging.info(f"Fetching dataset '{dataset_name}' from HuggingFace Hub...")
    
    try:
        # Load the dataset from HuggingFace
        # We use streaming=False to ensure we get the full dataset for processing, 
        # but we could use streaming=True if memory is a concern and we process in chunks.
        # For this specific task, we assume the dataset fits in memory or we handle it appropriately.
        dataset = load_dataset(dataset_name)
        
        # The dataset might be a dict of splits (e.g., 'train', 'test'). 
        # We'll take the 'train' split if available, otherwise the first one.
        if isinstance(dataset, dict):
            if "train" in dataset:
                df = dataset["train"].to_pandas()
            else:
                first_key = next(iter(dataset))
                df = dataset[first_key].to_pandas()
        else:
            df = dataset.to_pandas()
        
        # Normalize column names to lowercase to handle potential casing issues
        df.columns = [col.lower() for col in df.columns]
        
        # Validate required columns
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            error_msg = f"Dataset missing required columns: {missing_cols}. Found columns: {list(df.columns)}"
            logging.error(error_msg)
            raise ValueError(error_msg)
        
        # Prepare the output DataFrame
        output_df = pd.DataFrame()
        output_df["story_id"] = df["story_id"]
        output_df["empathy_score"] = df["empathy_score"]
        output_df["moral_judgement_score"] = df["moral_judgement_score"]
        
        # Add participant_id if it exists, otherwise generate a deterministic one based on index
        if "participant_id" in df.columns:
            output_df["participant_id"] = df["participant_id"]
        else:
            # Generate a deterministic participant_id if not present
            # Using the index as a base for a unique ID
            output_df["participant_id"] = [f"participant_{i}" for i in range(len(df))]
        
        # Add text_reflection if it exists
        if "text_reflection" in df.columns:
            output_df["text_reflection"] = df["text_reflection"]
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save to CSV
        output_df.to_csv(output_path, index=False)
        logging.info(f"Successfully saved reader response data to {output_path}")
        
        return output_df

    except Exception as e:
        logging.error(f"Failed to fetch or process dataset '{dataset_name}': {e}")
        # Re-raise to fail loudly as per constraints
        raise

def fetch_all_datasets(): # Added to make sure all datasets are fetched
    stories = fetch_gutenberg_stories()
    responses = load_reader_response_data()
    tweets = fetch_moral_foundations_twitter()

    return stories, responses, tweets