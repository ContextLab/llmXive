"""
Embedding Generator for MulTaBench extension.

Implements CPU-only inference for:
- CLIP ViT-B/32 for images
- Sentence-BERT for text

Uses default precision and disables gradient tracking.
"""
import torch
import numpy as np
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import warnings

# Import project utilities
from utils.logging import get_logger, log_info, log_warning, log_error
from utils.memory_monitor import get_process_memory_mb, track_memory

# Suppress specific warnings for cleaner logs during model loading
warnings.filterwarnings("ignore", category=UserWarning, module="transformers")
warnings.filterwarnings("ignore", category=UserWarning, module="torch")

logger = get_logger(__name__)

class EmbeddingGenerator:
    """
    Generates frozen embeddings for images and text using CLIP and Sentence-BERT.
    Runs strictly on CPU with no gradient tracking.
    """

    def __init__(
        self,
        image_model_name: str = "openai/clip-vit-base-patch32",
        text_model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        device: str = "cpu",
        batch_size: int = 32,
        max_length: int = 512
    ):
        """
        Initialize the embedding generator.

        Args:
            image_model_name: HuggingFace model ID for CLIP image encoder.
            text_model_name: HuggingFace model ID for Sentence-BERT.
            device: Device to run inference on (default: 'cpu').
            batch_size: Batch size for inference.
            max_length: Maximum token length for text.
        """
        self.device = device
        self.batch_size = batch_size
        self.max_length = max_length
        self.image_model = None
        self.text_model = None
        self.image_processor = None
        self.text_processor = None

        log_info(f"Initializing EmbeddingGenerator on {device}")

    def load_models(self) -> None:
        """
        Load CLIP and Sentence-BERT models onto CPU.
        Ensures models are in eval mode and gradients are disabled.
        """
        if self.image_model is not None and self.text_model is not None:
            log_info("Models already loaded.")
            return

        try:
            log_info("Loading CLIP ViT-B/32 image encoder...")
            from transformers import CLIPModel, CLIPProcessor

            self.image_model = CLIPModel.from_pretrained(
                "openai/clip-vit-base-patch32",
                torch_dtype=torch.float32
            )
            self.image_processor = CLIPProcessor.from_pretrained(
                "openai/clip-vit-base-patch32"
            )
            self.image_model.to(self.device)
            self.image_model.eval()
            log_info("CLIP image encoder loaded successfully.")

            log_info("Loading Sentence-BERT text encoder...")
            from sentence_transformers import SentenceTransformer

            self.text_model = SentenceTransformer(
                "sentence-transformers/all-MiniLM-L6-v2",
                device=self.device
            )
            # Ensure model is in eval mode
            self.text_model.eval()
            log_info("Sentence-BERT text encoder loaded successfully.")

        except Exception as e:
            log_error(f"Failed to load models: {e}")
            raise

    @torch.no_grad()
    def generate_image_embeddings(
        self,
        images: List[Union[str, "PIL.Image.Image", np.ndarray]],
        batch_size: Optional[int] = None
    ) -> np.ndarray:
        """
        Generate embeddings for a list of images.

        Args:
            images: List of image paths, PIL Images, or numpy arrays.
            batch_size: Override default batch size.

        Returns:
            Numpy array of shape (N, embedding_dim).
        """
        if self.image_model is None:
            self.load_models()

        bs = batch_size or self.batch_size
        embeddings = []
        total = len(images)

        log_info(f"Processing {total} images for embeddings...")

        for i in range(0, total, bs):
            batch_imgs = images[i : i + bs]
            mem_before = get_process_memory_mb()

            try:
                # Prepare inputs
                inputs = self.image_processor(
                    images=batch_imgs,
                    return_tensors="pt",
                    padding=True,
                    truncation=True,
                    max_length=77
                )
                inputs = {k: v.to(self.device) for k, v in inputs.items()}

                # Inference
                outputs = self.image_model.get_image_features(**inputs)
                batch_emb = outputs.cpu().numpy()
                embeddings.append(batch_emb)

                mem_after = get_process_memory_mb()
                log_debug(f"Image batch {i//bs + 1} memory delta: {mem_after - mem_before:.1f} MB")

            except Exception as e:
                log_error(f"Error processing image batch starting at index {i}: {e}")
                raise

        if not embeddings:
            return np.array([])

        return np.vstack(embeddings)

    @torch.no_grad()
    def generate_text_embeddings(
        self,
        texts: List[str],
        batch_size: Optional[int] = None
    ) -> np.ndarray:
        """
        Generate embeddings for a list of text strings.

        Args:
            texts: List of text strings.
            batch_size: Override default batch size.

        Returns:
            Numpy array of shape (N, embedding_dim).
        """
        if self.text_model is None:
            self.load_models()

        bs = batch_size or self.batch_size
        embeddings = []
        total = len(texts)

        log_info(f"Processing {total} text samples for embeddings...")

        # Sentence-BERT encode method handles batching internally efficiently
        # but we can also chunk manually if needed. Using the built-in encode with batch_size.
        try:
            batch_embeddings = self.text_model.encode(
                texts,
                batch_size=bs,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=True
            )
            return batch_embeddings

        except Exception as e:
            log_error(f"Error processing text embeddings: {e}")
            raise

    def generate_embeddings(
        self,
        images: Optional[List[Union[str, "PIL.Image.Image", np.ndarray]]] = None,
        texts: Optional[List[str]] = None
    ) -> Dict[str, np.ndarray]:
        """
        Generate embeddings for available inputs (images, texts, or both).

        Args:
            images: List of images.
            texts: List of text strings.

        Returns:
            Dictionary with keys 'image_embeddings' and/or 'text_embeddings'.
        """
        result = {}

        if images is not None and len(images) > 0:
            result["image_embeddings"] = self.generate_image_embeddings(images)

        if texts is not None and len(texts) > 0:
            result["text_embeddings"] = self.generate_text_embeddings(texts)

        if not result:
            log_warning("No valid inputs provided for embedding generation.")

        return result
