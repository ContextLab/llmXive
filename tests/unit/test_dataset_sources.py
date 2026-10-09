def test_openml_wired_into_resolver_source_aggregation():
    # Regression guard: OpenML must remain in the resolver's source set, else the
    # coverage silently drops back to the pre-fix registries.
    import inspect

    from llmxive.librarian import dataset_resolver
    assert "search_openml" in inspect.getsource(dataset_resolver)


def test_extract_dataset_intents_filters_noise_keeps_real_names():
    # The resolver extracted requirement IDs / RFC-2119 keywords / file formats as
    # bogus "dataset intents" (FR-001, MUST, CSV, PNG), searched real sources for
    # garbage, found nothing, and the project fabricated for lack of a verified
    # source. The filter must drop the noise and keep genuine dataset names.
    from llmxive.librarian.dataset_resolver import (
        _is_dataset_intent,
        extract_dataset_intents,
    )
    for noise in ["FR-001", "SC-015", "US1", "T044", "MUST", "CSV", "PNG",
                  "JSON", "API", "DOI", "PDF", "YAML"]:
        assert not _is_dataset_intent(noise), f"{noise} must be filtered"
    for real in ["HCP", "S1200", "QM9", "MNIST", "ImageNet", "NAB", "MBPP",
                 "CIFAR10"]:
        assert _is_dataset_intent(real), f"{real} must be kept"
    spec = ("The analysis MUST load the HCP S1200 dataset (see FR-001); the "
            "dataset export is CSV + PNG.")
    intents = extract_dataset_intents(spec)
    assert "HCP" in intents and "S1200" in intents
    for noise in ("FR-001", "MUST", "CSV", "PNG"):
        assert noise not in intents


def test_extract_dataset_intents_catches_camelcase_dataset_names():
    # CamelCase ML/NLP dataset names (ImageNet, WikiText, OpenWebText) were silently
    # missed by the acronym-only regex, so those specs resolved to nothing and the
    # project fabricated. They must now be extracted — but CamelCase tools / libs /
    # classes (PyTorch, GitHub, DataFrame) must NOT be surfaced as datasets.
    from llmxive.librarian.dataset_resolver import (
        _is_dataset_intent,
        extract_dataset_intents,
    )
    for real in ["ImageNet", "WikiText", "OpenWebText"]:
        assert _is_dataset_intent(real), f"{real} must be kept"
    for tool in ["PyTorch", "TensorFlow", "GitHub", "HuggingFace", "DataFrame",
                 "DataLoader"]:
        assert not _is_dataset_intent(tool), f"{tool} must be filtered"
    line = "The dataset loads ImageNet and WikiText via PyTorch DataLoader from GitHub."
    intents = extract_dataset_intents(line)
    assert "ImageNet" in intents and "WikiText" in intents


def test_extract_dataset_intents_filters_formats_and_model_names():
    # Domain FILE FORMATS and statistical/ML MODEL/METRIC names are NOT datasets;
    # extracting them fuzzy-matched unrelated real datasets that then "verified"
    # (CIF->cifar10, ARIMA->an anime set, GMM->GMM-Sefai, MSE->alpaca-es), so the
    # study loaded the wrong data. They must be filtered — WITHOUT filtering real
    # dataset names that merely embed a format token (CIFAR10, not CIF).
    from llmxive.librarian.dataset_resolver import (
        _is_dataset_intent,
        extract_dataset_intents,
    )
    for fmt in ["CIF", "VCF", "SDF", "BAM", "FASTQ", "NIfTI", "DICOM", "PDB"]:
        assert not _is_dataset_intent(fmt), f"format {fmt} must be filtered"
    for method in ["ARIMA", "GMM", "DP-GMM", "ADVI", "MSE", "RMSE", "ANOVA",
                   "PCA", "SVM", "LSTM", "GNN"]:
        assert not _is_dataset_intent(method), f"method/metric {method} must be filtered"
    # Real dataset names that embed or resemble a format/method token are KEPT.
    for real in ["CIFAR10", "QM9", "HCP", "ImageNet"]:
        assert _is_dataset_intent(real), f"{real} must be kept"
    spec = ("We fit an ARIMA model and a GMM, reporting MSE; the crystal dataset "
            "ships as CIF while the genomics dataset ships as VCF.")
    intents = extract_dataset_intents(spec)
    for noise in ("ARIMA", "GMM", "MSE", "CIF", "VCF"):
        assert noise not in intents
    for tool in ("PyTorch", "GitHub", "DataLoader"):
        assert tool not in intents
