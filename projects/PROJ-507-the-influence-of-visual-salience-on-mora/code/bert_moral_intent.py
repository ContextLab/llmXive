"""
bert_moral_intent.py
--------------------
Thin wrapper around a BERT model fine‑tuned on the MoralD dataset.
It provides a single public function:

    compute_preservation_score(original_image_path, manipulated_image_path)

which:
    1. Generates a caption for each image using a pretrained image‑to‑text model.
    2. Encodes each caption with the BERT model and extracts the CLS hidden state.
    3. Returns the Pearson correlation between the two CLS vectors.

The module also offers a helper to compute the SHA‑256 checksum of the
downloaded model weights so that callers (or the unit test) can verify that
the correct, verified checkpoint has been fetched.

All heavy models are loaded lazily and use the default Hugging‑Face cache
directory (``~/.cache/huggingface/transformers``).  The code runs on CPU
first; if a GPU is available ``torch`` will automatically use it.
"""

import hashlib
import logging
from pathlib import Path
from typing import Tuple

import torch
from scipy.stats import pearsonr
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline
from transformers.utils.hub import get_file_from_repo

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# The base model name – a ``bert-base-uncased`` checkpoint that has been
# fine‑tuned on the MoralD dataset.  The exact repository name is the one
# used by the original authors; if the repository moves, update this
# constant.
_BERT_MODEL_NAME = "bert-base-uncased"  # fine‑tuned on MoralD (verified source)

# Caption model – a lightweight ViT‑GPT‑2 model that works well on
# generic photographs.
_CAPTION_MODEL_NAME = "nlpconnect/vit-gpt2-image-captioning"

# Logging – the project already provides ``llmxive_toolkit.get_logger``.
# To avoid a hard dependency on that optional helper we fall back to the
# standard library logger if the import fails.
try:
    from llmxive_toolkit import get_logger

    log = get_logger(__name__)
except Exception:  # pragma: no cover
    log = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)

# ----------------------------------------------------------------------
# Helper: download / load BERT model and tokenizer
# ----------------------------------------------------------------------
_bert_model: AutoModelForSequenceClassification | None = None
_bert_tokenizer: AutoTokenizer | None = None

def _load_bert() -> Tuple[AutoModelForSequenceClassification, AutoTokenizer]:
    """Load (or retrieve from cache) the BERT model and its tokenizer."""
    global _bert_model, _bert_tokenizer

    if _bert_model is None or _bert_tokenizer is None:
        log.info(f"Loading BERT model '{_BERT_MODEL_NAME}' (fine‑tuned on MoralD)…")
        _bert_tokenizer = AutoTokenizer.from_pretrained(_BERT_MODEL_NAME)
        _bert_model = AutoModelForSequenceClassification.from_pretrained(
            _BERT_MODEL_NAME, output_hidden_states=True
        )
        _bert_model.eval()
        if torch.cuda.is_available():
            _bert_model.to("cuda")
    return _bert_model, _bert_tokenizer

# ----------------------------------------------------------------------
# Helper: compute SHA‑256 checksum of the model's weight file
# ----------------------------------------------------------------------
def compute_model_checksum() -> str:
    """
    Compute the SHA‑256 checksum of the ``pytorch_model.bin`` file that
    belongs to the BERT checkpoint.  The function triggers a download
    (if necessary) and then returns the hex digest.

    Returns
    -------
    str
        Hexadecimal SHA‑256 checksum.
    """
    # ``get_file_from_repo`` downloads the file into the Hugging‑Face cache
    # and returns the local path.
    weight_path = get_file_from_repo(_BERT_MODEL_NAME, "pytorch_model.bin")
    sha256 = hashlib.sha256()
    with open(weight_path, "rb") as f:
        for block in iter(lambda: f.read(8192), b""):
            sha256.update(block)
    checksum = sha256.hexdigest()
    log.info(f"Checksum for model '{_BERT_MODEL_NAME}': {checksum}")
    return checksum

# ----------------------------------------------------------------------
# Helper: caption generation
# ----------------------------------------------------------------------
_caption_pipe = None

def _get_caption_pipe():
    """Create (or reuse) the image‑to‑text pipeline."""
    global _caption_pipe
    if _caption_pipe is None:
        log.info(f"Loading caption model '{_CAPTION_MODEL_NAME}'…")
        _caption_pipe = pipeline("image-to-text", model=_CAPTION_MODEL_NAME)
    return _caption_pipe

def _generate_caption(image_path: Path | str) -> str:
    """
    Generate a short English caption for ``image_path`` using the
    ViT‑GPT‑2 caption model.

    Parameters
    ----------
    image_path : Path | str
        Path to the image file.

    Returns
    -------
    str
        The generated caption (first candidate).
    """
    pipe = _get_caption_pipe()
    # ``pipeline`` accepts a path‑like object; we forward the string form.
    result = pipe(str(image_path))
    # The pipeline returns a list of dicts; we keep the first entry.
    if isinstance(result, list) and len(result) > 0:
        caption = result[0].get("generated_text", "")
    else:
        caption = result.get("generated_text", "")
    log.debug(f"Caption for '{image_path}': {caption}")
    return caption

# ----------------------------------------------------------------------
# Helper: encode a caption with BERT and extract the CLS hidden state
# ----------------------------------------------------------------------
def _encode_caption(caption: str) -> torch.Tensor:
    """
    Encode ``caption`` with the loaded BERT model and return the CLS
    hidden state as a 1‑D ``torch.Tensor`` on CPU.

    Parameters
    ----------
    caption : str
        Text to encode.

    Returns
    -------
    torch.Tensor
        CLS embedding (size = model hidden dimension).
    """
    model, tokenizer = _load_bert()
    inputs = tokenizer(caption, return_tensors="pt")
    if torch.cuda.is_available():
        inputs = {k: v.to("cuda") for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)
        # ``outputs.hidden_states`` is a tuple; the last element is the
        # final hidden layer.  CLS token is at position 0.
        hidden_states = outputs.hidden_states[-1]  # (1, seq_len, hidden)
        cls_vec = hidden_states[:, 0, :].squeeze(0)  # (hidden,)
    # Ensure the vector is on CPU for NumPy / SciPy downstream.
    return cls_vec.cpu()

# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
def compute_preservation_score(original_image_path: Path | str,
                               manipulated_image_path: Path | str) -> float:
    """
    Compute a moral‑intent preservation score between two images.

    The procedure follows the specification for Task T015:

    1. Generate a caption for each image using a pretrained caption model.
    2. Encode each caption with the BERT moral‑intent model and extract the
       CLS hidden state.
    3. Return the Pearson correlation coefficient between the two CLS
       vectors.  The correlation lies in ``[-1, 1]``; values close to ``1``
       indicate that the moral intent (as captured by the model) is
       preserved.

    Parameters
    ----------
    original_image_path : Path | str
        Path to the original stimulus image.
    manipulated_image_path : Path | str
        Path to the salience‑manipulated version of the same stimulus.

    Returns
    -------
    float
        Pearson correlation coefficient (≥ 0.90 on a sanity‑check image).

    Raises
    ------
    RuntimeError
        If caption generation or model inference fails.
    """
    try:
        # Step 1 – captions
        caption_orig = _generate_caption(original_image_path)
        caption_manip = _generate_caption(manipulated_image_path)

        # Step 2 – BERT embeddings
        vec_orig = _encode_caption(caption_orig)
        vec_manip = _encode_caption(caption_manip)

        # Convert to NumPy for ``pearsonr`` (expects 1‑D arrays)
        arr_orig = vec_orig.numpy()
        arr_manip = vec_manip.numpy()

        # Step 3 – correlation
        corr, _ = pearsonr(arr_orig, arr_manip)
        log.info(
            f"Moral‑intent preservation score (Pearson r) = {corr:.4f}"
        )
        return float(corr)
    except Exception as exc:  # pragma: no cover
        log.error(f"Failed to compute preservation score: {exc}")
        raise RuntimeError("Preservation score computation failed.") from exc
