"""
Coarse Store Implementation for llmXive MemLens Benchmark.

This module implements the 'Coarse' memory store strategy as defined in
Constitution VI: load text summaries only, discarding all image data.
"""

import os
import json
import pickle
from typing import List, Dict, Any, Optional

import config


class CoarseStore:
    """
    A memory store that loads and manages text summaries from the MemLens dataset,
    explicitly discarding image data to minimize memory footprint and focus on
    textual reasoning.

    Attributes:
        data_path (str): Path to the raw data directory.
        output_path (str): Path to the output directory for processed stores.
        store_name (str): Identifier for this store type.
        index (List[Dict]): The loaded and processed data index.
    """

    def __init__(self, data_path: Optional[str] = None, output_path: Optional[str] = None):
        """
        Initializes the CoarseStore.

        Args:
            data_path: Path to raw data. Defaults to config.DATA_PATH.
            output_path: Path for processed outputs. Defaults to config.OUTPUT_PATH.
        """
        self.data_path = data_path or config.DATA_PATH
        self.output_path = output_path or config.OUTPUT_PATH
        self.store_name = "coarse"
        self.index: List[Dict[str, Any]] = []
        self._is_loaded = False

    def load(self, raw_data_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Loads the MemLens dataset, filters for relevant task types, and extracts
        ONLY the text summaries, discarding all image data (Constitution VI).

        Args:
            raw_data_path: Optional path to the raw JSON/JSONL file. If None,
                           attempts to load from data/raw based on project config.

        Returns:
            List[Dict]: A list of dictionaries containing only text summary data.

        Raises:
            FileNotFoundError: If the raw data file cannot be found.
            ValueError: If the data format is invalid.
        """
        if raw_data_path is None:
            # Assuming data_loader.py has placed the filtered raw data here
            # or we look for the standard MemLens file in the raw directory
            possible_paths = [
                os.path.join(self.data_path, "memlens_filtered.json"),
                os.path.join(self.data_path, "memlens.json"),
                os.path.join(self.data_path, "memlens_filtered.jsonl")
            ]
            found = False
            for p in possible_paths:
                if os.path.exists(p):
                    raw_data_path = p
                    found = True
                    break
            if not found:
                raise FileNotFoundError(
                    f"Raw data file not found in {self.data_path}. "
                    "Please ensure T005 (data_loader) has been executed."
                )

        self.index = []
        self._is_loaded = False

        # Determine file type and load
        if raw_data_path.endswith(".json"):
            with open(raw_data_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
        elif raw_data_path.endswith(".jsonl"):
            raw_data = []
            with open(raw_data_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        raw_data.append(json.loads(line))
        else:
            raise ValueError(f"Unsupported file format: {raw_data_path}")

        # Process and filter: Extract text summaries, discard images
        processed_count = 0
        for item in raw_data:
            # Validate required fields
            if "id" not in item or "summary" not in item:
                # Skip malformed entries but log if necessary
                continue

            # Constitution VI: Discard all image data
            # We explicitly do NOT extract or store 'image', 'image_path', or 'pixels'
            coarse_entry = {
                "id": item["id"],
                "summary": item["summary"],
                "task_type": item.get("task_type", "unknown"),
                "session_id": item.get("session_id", None),
                "ground_truth": item.get("ground_truth", None),
                "metadata": {
                    "source": "memlens",
                    "store_type": "coarse",
                    "discarded_fields": ["image", "image_path", "pixels"]
                }
            }

            # Optional: Filter by task type if not already done by data_loader
            # T005 already filters for ["Multi-Session Reasoning", "Temporal Reasoning"]
            # We trust that filter, but keep the check for safety
            if coarse_entry["task_type"] in ["Multi-Session Reasoning", "Temporal Reasoning"]:
                self.index.append(coarse_entry)
                processed_count += 1

        self._is_loaded = True
        return self.index

    def get_context(self, query_id: str, top_k: Optional[int] = None) -> str:
        """
        Retrieves the text context for a given query ID.
        Since this is a store, we assume a simple lookup or a basic retrieval
        mechanism (e.g., exact ID match or keyword search on summary).
        For the purpose of this benchmark, we return the summary associated
        with the ID if found, or a generic "No context found" message.

        In a full retrieval system, this would use FAISS (T010) to find
        similar summaries. Here we implement a basic retrieval interface
        that returns the relevant context string.

        Args:
            query_id: The ID of the query to retrieve context for.
            top_k: Ignored in this simple implementation but kept for interface compatibility.

        Returns:
            str: The text summary context.
        """
        if not self._is_loaded:
            raise RuntimeError("Store must be loaded before retrieving context.")

        # Simple exact match for now. In a real scenario, this would be vector search.
        # However, for the 'Coarse' store, we often just return the summary of the
        # relevant session if the query ID matches the session ID.
        for entry in self.index:
            if entry["id"] == query_id:
                return entry["summary"]

        # If not found by ID, return empty context or a message
        return "[No context found for query ID]"

    def build_index(self) -> None:
        """
        Builds an in-memory index for fast retrieval.
        For CoarseStore, since we only have text, we might prepare for
        vectorization later, but for now, the index is just the loaded list.
        This method satisfies the interface required by the pipeline.
        """
        if not self._is_loaded:
            raise RuntimeError("Store must be loaded before building index.")
        # No complex indexing needed for text-only summary store in this phase
        # The 'index' attribute already holds the data.
        pass

    def save_index(self, output_file: Optional[str] = None) -> str:
        """
        Saves the processed index to a file for later reuse.

        Args:
            output_file: Optional path to save the index. Defaults to
                         outputs/coarse_store_index.pkl.

        Returns:
            str: The path to the saved file.
        """
        if not self._is_loaded:
            raise RuntimeError("Store must be loaded before saving.")

        if output_file is None:
            os.makedirs(self.output_path, exist_ok=True)
            output_file = os.path.join(self.output_path, f"{self.store_name}_store_index.pkl")

        with open(output_file, "wb") as f:
            pickle.dump(self.index, f)

        return output_file

    def load_index(self, input_file: Optional[str] = None) -> None:
        """
        Loads the index from a saved file.

        Args:
            input_file: Optional path to the saved index file.
        """
        if input_file is None:
            input_file = os.path.join(self.output_path, f"{self.store_name}_store_index.pkl")

        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Saved index not found at {input_file}")

        with open(input_file, "rb") as f:
            self.index = pickle.load(f)

        self._is_loaded = True