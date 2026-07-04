import os
import sys
import requests
import pandas as pd
from typing import Optional

# Import existing functions from the same module as per API surface
# (Defined later in this file)
def filter_antibiotic_use(df: pd.DataFrame) -> pd.DataFrame:
  """Filter out samples with recent antibiotic use."""
  return df[~df['antibiotic_use_last_3m'].fillna(False)]

def filter_sleep_data(df: pd.DataFrame) -> pd.DataFrame:
  """Filter out samples with missing sleep metrics."""
  return df.dropna(subset=['sleep_efficiency', 'sleep_duration_hours'])


def verify_data_source_url(url: str) -> bool:
    """
    Verify the existence of the data source URL.
    
    Checks if the URL is accessible (HTTP 200) and points to a valid resource.
    
    Args:
        url: The URL to verify.
        
    Returns:
        True if the URL is accessible.
        
    Raises:
        FileNotFoundError: If the URL is not accessible or returns an error status.
        ValueError: If the URL is empty.
    """
    if not url or not url.strip():
        raise ValueError("Data source URL is empty or not configured.")
    
    try:
        # Use a HEAD request to check existence without downloading the full file
        response = requests.head(url, timeout=30, allow_redirects=True)
        
        # Check for successful response
        if response.status_code == 200:
            return True
        elif response.status_code == 404:
            raise FileNotFoundError(f"Data source URL not found (404): {url}")
        elif response.status_code == 403:
            raise FileNotFoundError(f"Data source URL forbidden (403): {url}")
        else:
            raise FileNotFoundError(f"Data source URL returned unexpected status {response.status_code}: {url}")
            
    except requests.exceptions.ConnectionError:
        raise FileNotFoundError(f"Could not connect to data source URL: {url}")
    except requests.exceptions.Timeout:
        raise FileNotFoundError(f"Connection to data source URL timed out: {url}")
    except requests.exceptions.RequestException as e:
        raise FileNotFoundError(f"Failed to verify data source URL: {e}")


def main():
    """
    Entry point for T012a: Data Feasibility Check.
    
    Verifies the existence of the verified data source URL from environment.
    Exits with code 1 if missing or inaccessible.
    """
    # Retrieve URL from environment variable (as per T005 config pattern)
    # Defaulting to a known real dataset for this project:
    # The Human Microbiome Project (HMP) or similar open repositories.
    # For this implementation, we use a specific URL from the HMP DACC or similar
    # that contains the required columns.
    # Since plan.md refers to a "verified datasets" block, we assume the URL
    # is provided via DATA_URL or a specific variable. 
    # Using a robust fallback to a real, public CSV for testing feasibility if env is unset,
    # but strictly enforcing the check as requested.
    
    # We will use a specific public dataset URL that matches the schema requirements
    # for this project's feasibility check.
    # Example: A subset of the HMP or a merged dataset from a public repo like Figshare or Zenodo
    # that includes 'antibiotic_use_last_3m', 'sleep_efficiency', 'sleep_duration_hours'.
    # Since a specific URL isn't in the prompt's snippet, we use a standard public health dataset
    # structure or a placeholder that *would* be replaced by the real plan.md URL.
    # To satisfy "Real data only" and "Fail loudly", we attempt to access a known public resource.
    # We will use the 'Gut Microbiome and Sleep' dataset often cited in open repositories.
    # Let's assume the URL is passed via environment variable DATA_URL.
    
    data_url = os.getenv("DATA_URL")
    
    if not data_url:
        # If no URL is provided in env, we cannot proceed with a real check.
        # However, to ensure the script runs and checks a REAL source as per constraints,
        # we might need to default to a known public URL if the plan implies one exists.
        # Given the strict "Real data" constraint, we will raise an error if not configured,
        # simulating the "missing from plan.md" scenario.
        # BUT, to make this task executable and demonstrate the check, we will define
        # a known valid URL for a public dataset that *should* be in the plan.
        # We'll use a Zenodo record or similar that is publicly accessible.
        # For the purpose of this specific task implementation without the full plan.md text,
        # we will define a constant that represents the "Verified URL" and check it.
        # If the real project plan has a different URL, the env var should override.
        
        # Fallback to a real, public dataset URL for the feasibility check demonstration.
        # This URL points to a CSV with microbiome and metadata (simulated for structure).
        # In a real scenario, this would be the exact URL from plan.md.
        data_url = "https://zenodo.org/record/4567890/files/microbiome_sleep_data.csv" 
        # Note: The above is a placeholder structure. 
        # To be strictly compliant with "Real data", we must find a real URL.
        # Let's use a real, accessible dataset from a known source like the HMP or a specific paper's supplement.
        # Since I cannot browse the live web to find a *current* specific CSV with those exact columns
        # without risking a 404 later, I will implement the logic to check the URL provided.
        # If the user expects this to run against a specific real URL, they must set DATA_URL.
        # However, to avoid "fabricating", I will raise FileNotFoundError if the URL is not set
        # or if the fallback (if I were to provide one) fails.
        
        # Re-reading constraint: "If missing, raise FileNotFoundError and exit with code 1."
        # If the plan.md doesn't have it, we fail.
        # I will assume the environment variable DATA_URL is the source of truth.
        # If it is not set, we treat it as missing.
        print("ERROR: DATA_URL environment variable is not set.")
        print("The verified data source URL is missing from the configuration.")
        sys.exit(1)

    print(f"Verifying data source URL: {data_url}")
    
    try:
        verify_data_source_url(data_url)
        print("SUCCESS: Data source URL is accessible.")
        sys.exit(0)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Unexpected error during verification: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
