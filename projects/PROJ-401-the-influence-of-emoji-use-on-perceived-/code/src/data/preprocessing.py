import logging
import re
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
import emoji
import numpy as np

logger = logging.getLogger(__name__)

def extract_emoji_features(text: str) -> Dict[str, Any]:
    """
    Extract emoji-related features from a given text string.

    Args:
        text (str): The input text message.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - 'emoji_present' (bool): True if any emoji found.
            - 'emoji_count' (int): Total number of emoji characters.
            - 'emoji_types' (List[str]): List of unique emoji characters found.
    """
    if not isinstance(text, str) or len(text) == 0:
        logger.warning(f"Invalid or empty text provided for emoji extraction: {repr(text)}")
        return {
            'emoji_present': False,
            'emoji_count': 0,
            'emoji_types': []
        }

    try:
        # Normalize text to ensure consistent emoji representation
        normalized_text = emoji.replace_emoji(text, replacement='')
        # Get all emojis in the text
        emojis = emoji.emoji_list(text)
        
        if not emojis:
            logger.debug(f"No emojis found in text: {text[:50]}...")
            return {
                'emoji_present': False,
                'emoji_count': 0,
                'emoji_types': []
            }

        # Extract the actual emoji characters
        emoji_chars = [e['emoji'] for e in emojis]
        unique_emojis = list(set(emoji_chars))
        
        result = {
            'emoji_present': True,
            'emoji_count': len(emoji_chars),
            'emoji_types': unique_emojis
        }
        
        logger.debug(f"Extracted {len(emoji_chars)} emojis from text: {text[:50]}...")
        return result

    except Exception as e:
        logger.error(f"Error extracting emoji features from text '{text[:50]}...': {str(e)}", exc_info=True)
        # Return default safe values on error to prevent pipeline halt
        return {
            'emoji_present': False,
            'emoji_count': 0,
            'emoji_types': []
        }

def preprocess_dataframe(df: pd.DataFrame, text_column: str = 'text') -> pd.DataFrame:
    """
    Preprocess a DataFrame by adding emoji features to each row.
    
    This function applies extract_emoji_features to each row and adds the
    resulting features as new columns. It includes robust error handling
    and logging for skipped records.

    Args:
        df (pd.DataFrame): Input DataFrame containing text messages.
        text_column (str): Name of the column containing text messages.

    Returns:
        pd.DataFrame: DataFrame with added emoji feature columns:
            - 'emoji_present' (bool)
            - 'emoji_count' (int)
            - 'emoji_types' (str): JSON string of list of emoji types

    Raises:
        ValueError: If the specified text_column is not found in the DataFrame.
    """
    import pandas as pd
    import json

    if text_column not in df.columns:
        logger.error(f"Text column '{text_column}' not found in DataFrame. Available columns: {list(df.columns)}")
        raise ValueError(f"Text column '{text_column}' not found in DataFrame")

    logger.info(f"Starting emoji feature extraction for {len(df)} records...")
    
    extracted_features = []
    skipped_count = 0
    error_count = 0

    for idx, row in df.iterrows():
        try:
            text = row[text_column]
            
            # Handle None or non-string values
            if pd.isna(text) or not isinstance(text, str):
                logger.warning(f"Skipping row {idx}: Invalid text value (type: {type(text).__name__}, value: {repr(text)})")
                skipped_count += 1
                extracted_features.append({
                    'emoji_present': False,
                    'emoji_count': 0,
                    'emoji_types': []
                })
                continue

            features = extract_emoji_features(text)
            extracted_features.append(features)

        except Exception as e:
            logger.error(f"Error processing row {idx}: {str(e)}", exc_info=True)
            error_count += 1
            # Append safe defaults for failed rows
            extracted_features.append({
                'emoji_present': False,
                'emoji_count': 0,
                'emoji_types': []
            })

    # Log summary of processing
    logger.info(f"Emoji extraction complete. Processed: {len(df)}, Skipped: {skipped_count}, Errors: {error_count}")
    
    if error_count > 0:
        logger.warning(f"{error_count} records encountered errors during emoji extraction. Check logs for details.")
    
    if skipped_count > 0:
        logger.info(f"{skipped_count} records were skipped due to invalid text values.")

    # Convert features to DataFrame and concatenate
    features_df = pd.DataFrame(extracted_features)
    
    # Convert emoji_types list to JSON string for CSV compatibility
    features_df['emoji_types'] = features_df['emoji_types'].apply(lambda x: json.dumps(x) if isinstance(x, list) else '[]')
    
    # Ensure column order matches expected schema
    result_df = pd.concat([df, features_df], axis=1)
    
    logger.info(f"Preprocessing complete. Final DataFrame shape: {result_df.shape}")
    return result_df