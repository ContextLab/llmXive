"""
Medium Store Implementation for llmXive MemLens Benchmark.

This store loads text summaries and computes frozen CLIP embeddings for images.
It adheres to Constitution VI by retaining image-derived semantic information
while discarding raw pixel data after embedding computation.
"""

import os
import json
import pickle
from typing import List, Dict, Any, Optional

import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel

import config
from stores.base import MemoryStore


class MediumStore(MemoryStore):
    """
    Memory store that processes images using a frozen CLIP model to generate
    semantic embeddings. Text summaries are stored directly.

    Attributes:
        model: Frozen CLIP model for image embedding.
        processor: CLIP processor for image preprocessing.
        device: Computation device ('cpu' or 'cuda').
    """

    def __init__(self, model_name: str = "openai/clip-vit-base-patch32"):
        """
        Initialize the MediumStore with a frozen CLIP model.

        Args:
            model_name: HuggingFace model identifier for CLIP.
        """
        super().__init__()
        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        # Load frozen CLIP model
        self.model = CLIPModel.from_pretrained(self.model_name)
        self.model.eval()
        self.model.to(self.device)

        # Freeze parameters
        for param in self.model.parameters():
            param.requires_grad = False

        self.processor = CLIPProcessor.from_pretrained(self.model_name)

        self.index: List[Dict[str, Any]] = []

    def load_data(self, data_path: str) -> None:
        """
        Load data from the specified path, computing CLIP embeddings for images.

        Args:
            data_path: Path to the directory containing raw data JSON/JSONL files.
        """
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"Data path not found: {data_path}")

        # Assuming data_loader has already filtered and saved to data/processed
        # We look for the processed file or load from raw if processed doesn't exist yet
        processed_path = os.path.join(config.DATA_PATH, "processed", "mem_lens_filtered.json")
        
        if not os.path.exists(processed_path):
            # Fallback to raw if processed doesn't exist (though T005 should have created it)
            processed_path = os.path.join(config.DATA_PATH, "raw", "mem_lens_filtered.json")

        if not os.path.exists(processed_path):
            raise FileNotFoundError(f"Processed data file not found at {processed_path}. "
                                    "Ensure T005 (data_loader) has been executed.")

        with open(processed_path, "r", encoding="utf-8") as f:
            # Handle JSONL or JSON list
            data = []
            for line in f:
                data.append(json.loads(line))
            if not data and os.path.getsize(processed_path) > 0:
                # Try loading as a single JSON object/list if JSONL failed
                f.seek(0)
                data = json.load(f)

        for item in data:
            item_id = item.get("id")
            text_summary = item.get("summary", "")
            image_path = item.get("image_path")

            if not item_id or not text_summary:
                continue

            # Process image if path exists
            image_embedding = None
            if image_path and os.path.exists(image_path):
                try:
                    image = Image.open(image_path).convert("RGB")
                    inputs = self.processor(images=image, return_tensors="pt")
                    inputs = {k: v.to(self.device) for k, v in inputs.items()}

                    with torch.no_grad():
                        image_features = self.model.get_image_features(**inputs)
                        # Normalize embeddings for cosine similarity
                        image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                    
                    image_embedding = image_features.cpu().numpy().flatten().tolist()
                except Exception as e:
                    print(f"Warning: Failed to process image {image_path} for item {item_id}: {e}")

            record = {
                "id": item_id,
                "summary": text_summary,
                "image_embedding": image_embedding,
                "metadata": item.get("metadata", {})
            }
            self.index.append(record)

    def get_context(self, query_id: str, top_k: int = 5) -> str:
        """
        Retrieve context for a query.
        In a real retrieval scenario, this would query the FAISS index.
        For this implementation, we return a placeholder indicating the retrieval logic
        is handled by the retrieval.py module which consumes the embeddings.
        
        Args:
            query_id: The ID of the query.
            top_k: Number of top results to retrieve.
        
        Returns:
            A string representation of the retrieved context.
        """
        # This method is primarily for interface compatibility.
        # Actual retrieval logic using embeddings is in retrieval.py.
        # We return a status message indicating the store is ready for retrieval.
        return f"MediumStore context for {query_id} (Retrieval handled by retrieval.py)"

    def build_index(self) -> None:
        """
        Build the FAISS index using the computed image embeddings.
        This method is called by the retrieval module or run_pipeline.
        """
        import faiss
        import numpy as np

        # Collect all non-null embeddings
        embeddings = []
        valid_ids = []
        
        for record in self.index:
            if record.get("image_embedding") is not None:
                embeddings.append(record["image_embedding"])
                valid_ids.append(record["id"])

        if not embeddings:
            print("Warning: No valid image embeddings found to build index.")
            self.faiss_index = None
            return

        embeddings_np = np.array(embeddings, dtype=np.float32)
        dimension = embeddings_np.shape[1]
        
        # Create FAISS index for cosine similarity (L2 distance on normalized vectors)
        self.faiss_index = faiss.IndexFlatL2(dimension)
        self.faiss_index.add(embeddings_np)
        self.valid_ids = valid_ids

    def save(self, output_path: str) -> None:
        """
        Save the store state to disk.

        Args:
            output_path: Path to save the pickle file.
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            pickle.dump({
                "index": self.index,
                "model_name": self.model_name,
                "valid_ids": getattr(self, "valid_ids", [])
            }, f)

    @classmethod
    def load(cls, path: str) -> "MediumStore":
        """
        Load a store from disk.

        Args:
            path: Path to the pickle file.

        Returns:
            Loaded MediumStore instance.
        """
        with open(path, "rb") as f:
            data = pickle.load(f)
        
        store = cls(model_name=data["model_name"])
        store.index = data["index"]
        store.valid_ids = data["valid_ids"]
        return store
