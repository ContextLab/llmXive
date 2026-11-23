"""
Data loading utilities for Sleep-EDF preprocessing pipeline.

Provides efficient loading and iteration over processed epochs and transition windows
stored in Parquet format.
"""

import os
import gc
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Iterator, Any

import numpy as np
import pandas as pd

from src.utils.config import get_paths, get_data_config
from src.utils.logging import get_logger


logger = get_logger(__name__)


class EpochLoader:
    """
    Loader for processed sleep epochs and transition windows.

    Handles loading data from Parquet files with support for:
    - Lazy loading (streaming)
    - Subject-based grouping
    - Channel selection
    - Memory-efficient iteration
    """

    def __init__(
        self,
        epochs_path: Optional[Union[str, Path]] = None,
        transition_windows_path: Optional[Union[str, Path]] = None,
        pre_transition_path: Optional[Union[str, Path]] = None,
        eog_path: Optional[Union[str, Path]] = None,
        subject_ids: Optional[List[str]] = None,
        channels: Optional[List[str]] = None,
        streaming: bool = True
    ):
        """
        Initialize the EpochLoader.

        Args:
            epochs_path: Path to stable epochs Parquet file
            transition_windows_path: Path to centered transition windows Parquet file
            pre_transition_path: Path to pre-transition windows Parquet file (for model training)
            eog_path: Path to EOG signals Parquet file
            subject_ids: List of subject IDs to load (None for all)
            channels: List of channel names to include (None for all)
            streaming: If True, use streaming mode for large datasets
        """
        paths = get_paths()
        data_config = get_data_config()

        # Use config defaults if paths not provided
        self.epochs_path = Path(epochs_path) if epochs_path else paths.processed / data_config.epochs_file
        self.transition_windows_path = Path(transition_windows_path) if transition_windows_path else paths.processed / data_config.transition_windows_file
        self.pre_transition_path = Path(pre_transition_path) if pre_transition_path else paths.processed / data_config.pre_transition_file
        self.eog_path = Path(eog_path) if eog_path else paths.processed / data_config.eog_file

        self.subject_ids = subject_ids
        self.channels = channels
        self.streaming = streaming

        # Validate files exist
        self._validate_files()

        logger.info(f"EpochLoader initialized with streaming={streaming}")
        logger.info(f"Epochs path: {self.epochs_path}")
        logger.info(f"Transition windows path: {self.transition_windows_path}")
        logger.info(f"Pre-transition windows path: {self.pre_transition_path}")
        logger.info(f"EOG path: {self.eog_path}")

    def _validate_files(self) -> None:
        """Validate that required data files exist."""
        missing = []
        if not self.epochs_path.exists():
            missing.append(str(self.epochs_path))
        if not self.transition_windows_path.exists():
            missing.append(str(self.transition_windows_path))
        if not self.pre_transition_path.exists():
            missing.append(str(self.pre_transition_path))

        if missing:
            raise FileNotFoundError(
                f"Required data files not found: {', '.join(missing)}. "
                f"Ensure preprocessing (T014, T014b) has been completed."
            )

        # EOG is optional
        if not self.eog_path.exists():
            logger.warning(f"EOG file not found: {self.eog_path}. EOG features will be unavailable.")

    def load_epochs(
        self,
        chunk_size: Optional[int] = None
    ) -> Iterator[pd.DataFrame]:
        """
        Load stable epochs from the epochs file.

        Args:
            chunk_size: Number of rows to load at a time (None for all)

        Yields:
            DataFrames containing epoch data
        """
        logger.info(f"Loading epochs from {self.epochs_path}")

        if self.streaming and chunk_size:
            # Stream in chunks
            for chunk in pd.read_parquet(
                self.epochs_path,
                columns=self.channels if self.channels else None
            ).groupby(np.arange(len(pd.read_parquet(self.epochs_path))) // chunk_size):
                df = chunk[1]
                if self.subject_ids:
                    df = df[df['subject_id'].isin(self.subject_ids)]
                if not df.empty:
                    yield df
                    del df
                    gc.collect()
        else:
            # Load all at once
            df = pd.read_parquet(
                self.epochs_path,
                columns=self.channels if self.channels else None
            )

            if self.subject_ids:
                df = df[df['subject_id'].isin(self.subject_ids)]

            yield df
            del df
            gc.collect()

    def load_transition_windows(
        self,
        window_type: str = 'centered'
    ) -> Iterator[pd.DataFrame]:
        """
        Load transition windows from the transition windows file.

        Args:
            window_type: Type of windows to load ('centered' or 'pre')

        Yields:
            DataFrames containing transition window data
        """
        if window_type == 'centered':
            path = self.transition_windows_path
        elif window_type == 'pre':
            path = self.pre_transition_path
        else:
            raise ValueError(f"Unknown window_type: {window_type}. Use 'centered' or 'pre'.")

        logger.info(f"Loading {window_type} transition windows from {path}")

        if not path.exists():
            raise FileNotFoundError(f"Transition windows file not found: {path}")

        # Load all at once (transition windows are smaller than full epochs)
        df = pd.read_parquet(
            path,
            columns=self.channels if self.channels else None
        )

        if self.subject_ids:
            df = df[df['subject_id'].isin(self.subject_ids)]

        yield df
        del df
        gc.collect()

    def load_eog_signals(self) -> Optional[pd.DataFrame]:
        """
        Load EOG signals if available.

        Returns:
            DataFrame with EOG signals, or None if EOG is unavailable
        """
        if not self.eog_path.exists():
            logger.warning("EOG file not found, returning None")
            return None

        logger.info(f"Loading EOG signals from {self.eog_path}")

        df = pd.read_parquet(self.eog_path)

        if self.subject_ids:
            df = df[df['subject_id'].isin(self.subject_ids)]

        return df

    def get_epoch_metadata(self) -> pd.DataFrame:
        """
        Get metadata for all epochs without loading signal data.

        Returns:
            DataFrame with epoch metadata (subject_id, stage, timestamp, etc.)
        """
        logger.info("Loading epoch metadata")

        # Read only metadata columns
        metadata_cols = ['subject_id', 'stage', 'timestamp', 'epoch_index', 'is_transition']
        df = pd.read_parquet(self.epochs_path, columns=metadata_cols)

        if self.subject_ids:
            df = df[df['subject_id'].isin(self.subject_ids)]

        return df

    def get_transition_metadata(self, window_type: str = 'centered') -> pd.DataFrame:
        """
        Get metadata for transition windows.

        Args:
            window_type: Type of windows ('centered' or 'pre')

        Returns:
            DataFrame with transition window metadata
        """
        if window_type == 'centered':
            path = self.transition_windows_path
        else:
            path = self.pre_transition_path

        logger.info(f"Loading {window_type} transition metadata from {path}")

        metadata_cols = ['subject_id', 'transition_stage_from', 'transition_stage_to', 
                       'transition_timestamp', 'window_index', 'is_valid']
        df = pd.read_parquet(path, columns=metadata_cols)

        if self.subject_ids:
            df = df[df['subject_id'].isin(self.subject_ids)]

        return df

    def iterate_by_subject(self, data_type: str = 'epochs') -> Iterator[Tuple[str, pd.DataFrame]]:
        """
        Iterate over data grouped by subject.

        Args:
            data_type: Type of data to load ('epochs', 'transition', 'pre_transition')

        Yields:
            Tuples of (subject_id, DataFrame)
        """
        if data_type == 'epochs':
            df_iter = self.load_epochs()
        elif data_type in ['transition', 'pre_transition']:
            window_type = 'centered' if data_type == 'transition' else 'pre'
            df_iter = self.load_transition_windows(window_type=window_type)
        else:
            raise ValueError(f"Unknown data_type: {data_type}")

        for df in df_iter:
            if df.empty:
                continue

            for subject_id in df['subject_id'].unique():
                subject_df = df[df['subject_id'] == subject_id].copy()
                yield subject_id, subject_df
                del subject_df
                gc.collect()


def load_processed_data(
    epochs_path: Optional[Union[str, Path]] = None,
    transition_windows_path: Optional[Union[str, Path]] = None,
    pre_transition_path: Optional[Union[str, Path]] = None,
    subject_ids: Optional[List[str]] = None,
    channels: Optional[List[str]] = None
) -> Dict[str, pd.DataFrame]:
    """
    Convenience function to load all processed data at once.

    Args:
        epochs_path: Path to stable epochs file
        transition_windows_path: Path to centered transition windows
        pre_transition_path: Path to pre-transition windows
        subject_ids: List of subject IDs to include
        channels: List of channels to include

    Returns:
        Dictionary with keys: 'epochs', 'transition_windows', 'pre_transition_windows'
    """
    loader = EpochLoader(
        epochs_path=epochs_path,
        transition_windows_path=transition_windows_path,
        pre_transition_path=pre_transition_path,
        subject_ids=subject_ids,
        channels=channels,
        streaming=False  # Load all at once for convenience function
    )

    data = {}

    # Load epochs
    epochs_list = list(loader.load_epochs())
    if epochs_list:
        data['epochs'] = epochs_list[0]
    else:
        data['epochs'] = pd.DataFrame()

    # Load transition windows
    transition_list = list(loader.load_transition_windows('centered'))
    if transition_list:
        data['transition_windows'] = transition_list[0]
    else:
        data['transition_windows'] = pd.DataFrame()

    # Load pre-transition windows
    pre_transition_list = list(loader.load_transition_windows('pre'))
    if pre_transition_list:
        data['pre_transition_windows'] = pre_transition_list[0]
    else:
        data['pre_transition_windows'] = pd.DataFrame()

    # Load EOG if available
    eog_df = loader.load_eog_signals()
    if eog_df is not None:
        data['eog'] = eog_df

    return data


def create_dataloader_for_training(
    pre_transition_path: Optional[Union[str, Path]] = None,
    subject_ids: Optional[List[str]] = None,
    channels: Optional[List[str]] = None,
    batch_size: int = 32,
    shuffle: bool = True
) -> Iterator[pd.DataFrame]:
    """
    Create an iterator for model training from pre-transition windows.

    This is specifically designed for T027 (model training) to consume
    the pre-transition windows generated in T014b.

    Args:
        pre_transition_path: Path to pre-transition windows file
        subject_ids: List of subject IDs to include
        channels: List of channels to include
        batch_size: Number of samples per batch
        shuffle: Whether to shuffle data

    Yields:
        Batches of data for training
    """
    loader = EpochLoader(
        pre_transition_path=pre_transition_path,
        subject_ids=subject_ids,
        channels=channels,
        streaming=False
    )

    # Load all pre-transition windows
    window_list = list(loader.load_transition_windows('pre'))
    if not window_list:
        logger.warning("No pre-transition windows found for training")
        return

    df = window_list[0]

    if shuffle:
        df = df.sample(frac=1, random_state=42).reset_index(drop=True)

    # Yield batches
    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i+batch_size]
        yield batch
        del batch
        gc.collect()


def main():
    """
    Main function to demonstrate loader usage and validate data loading.
    """
    logger.info("Running EpochLoader validation...")

    try:
        # Initialize loader
        loader = EpochLoader()

        # Test metadata loading
        logger.info("Testing epoch metadata loading...")
        epoch_meta = loader.get_epoch_metadata()
        logger.info(f"Loaded {len(epoch_meta)} epochs from {epoch_meta['subject_id'].nunique()} subjects")
        logger.info(f"Epoch stages: {epoch_meta['stage'].value_counts().to_dict()}")

        # Test transition window loading
        logger.info("Testing transition window loading...")
        transition_list = list(loader.load_transition_windows('centered'))
        if transition_list:
            logger.info(f"Loaded {len(transition_list[0])} centered transition windows")

        # Test pre-transition window loading
        logger.info("Testing pre-transition window loading...")
        pre_transition_list = list(loader.load_transition_windows('pre'))
        if pre_transition_list:
            logger.info(f"Loaded {len(pre_transition_list[0])} pre-transition windows")

        # Test subject iteration
        logger.info("Testing subject iteration...")
        subject_count = 0
        for subject_id, subject_df in loader.iterate_by_subject('epochs'):
            subject_count += 1
            if subject_count >= 3:  # Just test first 3 subjects
                break
        logger.info(f"Successfully iterated over {subject_count} subjects")

        # Test convenience function
        logger.info("Testing load_processed_data convenience function...")
        data = load_processed_data()
        logger.info(f"Loaded data keys: {list(data.keys())}")
        for key, df in data.items():
            logger.info(f"  {key}: {len(df)} rows")

        logger.info("EpochLoader validation completed successfully!")
        return True

    except FileNotFoundError as e:
        logger.error(f"Data files not found: {e}")
        logger.error("Please ensure preprocessing tasks (T014, T014b) have been completed first.")
        return False
    except Exception as e:
        logger.error(f"Error during validation: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
