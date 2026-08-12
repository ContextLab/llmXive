import os
import re
import json
import hashlib
import requests
import pandas as pd
import logging

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

def fetch_all_datasets(): # Added to make sure all datasets are fetched
    stories = fetch_gutenberg_stories()
    responses = load_reader_response_data()
    tweets = fetch_moral_foundations_twitter()

    return stories, responses, tweets
