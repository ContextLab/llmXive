"""
I/O utilities for the Glass Forming Region prediction project.

Handles loading/saving CSV and JSON data, and interacting with the 
Materials Project API (v3) for elemental and composition data.
"""
import csv
import json
import os
from typing import Any, Dict, List, Optional, Union
import requests

# Constants
MP_API_V3_BASE = "https://api.materialsproject.org/v3"
ENV_VAR_API_KEY = "MP_API_KEY"


def get_materials_project_api_key() -> str:
    """
    Retrieves the Materials Project API key from the environment variable.
    
    Raises:
        ValueError: If the API key is not set in the environment.
    """
    api_key = os.getenv(ENV_VAR_API_KEY)
    if not api_key:
        raise ValueError(
            f"Materials Project API key not found. "
            f"Please set the {ENV_VAR_API_KEY} environment variable."
        )
    return api_key


def load_csv(filepath: str) -> List[Dict[str, Any]]:
    """
    Loads a CSV file and returns a list of dictionaries.
    
    Args:
        filepath: Path to the CSV file.
        
    Returns:
        List of dictionaries where each dictionary represents a row.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        Exception: If there is an error reading the file.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"CSV file not found: {filepath}")
    
    data = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Attempt to convert numeric strings to float/int for cleaner data
            cleaned_row = {}
            for k, v in row.items():
                if v == '':
                    cleaned_row[k] = None
                else:
                    try:
                        # Try int first
                        cleaned_row[k] = int(v)
                    except ValueError:
                        try:
                            # Try float
                            cleaned_row[k] = float(v)
                        except ValueError:
                            # Keep as string
                            cleaned_row[k] = v
            data.append(cleaned_row)
    return data


def load_json(filepath: str) -> Union[Dict, List]:
    """
    Loads a JSON file and returns the parsed content.
    
    Args:
        filepath: Path to the JSON file.
        
    Returns:
        Parsed JSON content (dict or list).
        
    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"JSON file not found: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_csv(data: List[Dict[str, Any]], filepath: str) -> None:
    """
    Saves a list of dictionaries to a CSV file.
    
    Args:
        data: List of dictionaries to save.
        filepath: Path to the output CSV file.
    """
    if not data:
        # Create empty file if no data
        with open(filepath, 'w', encoding='utf-8') as f:
            pass
        return

    # Determine all unique keys
    fieldnames = list(data[0].keys())
    for row in data:
        fieldnames = sorted(set(fieldnames) | set(row.keys()))
    
    with open(filepath, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def save_json(data: Union[Dict, List], filepath: str) -> None:
    """
    Saves data to a JSON file with pretty printing.
    
    Args:
        data: Data to save (dict or list).
        filepath: Path to the output JSON file.
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def fetch_materials_project_elements(api_key: Optional[str] = None) -> Dict[str, Dict]:
    """
    Fetches elemental properties from the Materials Project API v3.
    
    Args:
        api_key: Optional API key. If not provided, reads from environment.
        
    Returns:
        Dictionary mapping element symbols to their properties.
        
    Raises:
        requests.RequestException: If the API request fails.
        ValueError: If the API key is invalid or missing.
    """
    if api_key is None:
        api_key = get_materials_project_api_key()
    
    url = f"{MP_API_V3_BASE}/elements"
    headers = {"X-API-Key": api_key}
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # The API returns a list of elements; normalize to a dict keyed by symbol
        elements = {}
        if "data" in data:
            for item in data["data"]:
                symbol = item.get("symbol")
                if symbol:
                    elements[symbol] = item
        return elements
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            raise ValueError("Invalid Materials Project API key.") from e
        raise
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to fetch elements from Materials Project: {e}") from e


def fetch_materials_project_composition(formula: str, api_key: Optional[str] = None) -> Optional[Dict]:
    """
    Fetches composition data (structure, energy, etc.) for a specific formula.
    
    Args:
        formula: Chemical formula (e.g., "Fe2O3").
        api_key: Optional API key. If not provided, reads from environment.
        
    Returns:
        Dictionary containing composition data, or None if not found.
        
    Raises:
        requests.RequestException: If the API request fails (excluding 404).
        ValueError: If the API key is invalid or missing.
    """
    if api_key is None:
        api_key = get_materials_project_api_key()
    
    # URL encode the formula just in case
    encoded_formula = requests.utils.quote(formula)
    url = f"{MP_API_V3_BASE}/materials/{encoded_formula}"
    headers = {"X-API-Key": api_key}
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 404:
            return None
        
        response.raise_for_status()
        data = response.json()
        
        # Return the 'data' object if present
        return data.get("data") if "data" in data else data
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            raise ValueError("Invalid Materials Project API key.") from e
        raise
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to fetch composition {formula} from Materials Project: {e}") from e