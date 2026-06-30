# Reproduce & validate: MulTaBench: Benchmarking Multimodal Tabular Learning with Text and Image

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-577-multabench-benchmarking-multimodal-tabul/external/MulTaBench/   (clone of https://github.com/alanarazi7/MulTaBench)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** MulTaBench: Benchmarking Multimodal Tabular Learning with Text and Image

**Abstract:** Tabular Foundation Models have recently established the state of the art in supervised tabular learning, by leveraging pretraining to learn generalizable representations of numerical and categorical structured data. However, they lack native support for unstructured modalities such as text and image, and rely on frozen, pretrained embeddings to process them. On established Multimodal Tabular Learning benchmarks, we show that tuning the embeddings to the task improves performance. Existing benchmarks, however, often focus on the mere co-occurrence of modalities; this leads to high variance across datasets and masks the benefits of task-specific tuning. To address this gap, we introduce MulTaBench, a benchmark of 40 datasets, split equally between image-tabular and text-tabular tasks. We focus on predictive tasks where the modalities provide complementary predictive signal, and where generic embeddings lose critical information, necessitating Target-Aware Representations that are aligned with the task. Our experimental results demonstrate that the gains from target-aware representation tuning generalize across both text and image modalities, several tabular learners, encoder scales, and embedding dimensions. MulTaBench constitutes the largest image-tabular benchmarking effort to date, spanning high-impact domains such as healthcare and e-commerce. It is designed to enable the research of novel architectures which incorporate joint modeling and target-aware representations, paving the way for the development of novel Multimodal Tabular Foundation Models.

## Shipped code — file tree (`projects/PROJ-577-multabench-benchmarking-multimodal-tabul/external/MulTaBench/`)

```
.env.example
.gitignore
README.md
benchmark.py
init.sh
multabench/__init__.py
multabench/baselines/__init__.py
multabench/baselines/abstract_model.py
multabench/baselines/autogluon_mm.py
multabench/baselines/benchmarks/__init__.py
multabench/baselines/benchmarks/evaluate.py
multabench/baselines/catboost.py
multabench/baselines/contexttab.py
multabench/baselines/lgbm.py
multabench/baselines/preprocessing/__init__.py
multabench/baselines/preprocessing/categorical.py
multabench/baselines/preprocessing/feature_types.py
multabench/baselines/preprocessing/image_embeddings.py
multabench/baselines/preprocessing/numerical.py
multabench/baselines/preprocessing/sampling.py
multabench/baselines/preprocessing/target.py
multabench/baselines/preprocessing/text_embeddings.py
multabench/baselines/random_forest.py
multabench/baselines/realmlp.py
multabench/baselines/tabdpt.py
multabench/baselines/tabicl_v2.py
multabench/baselines/tabm.py
multabench/baselines/tabpfnv2.py
multabench/baselines/tabstar_v1.py
multabench/baselines/training/__init__.py
multabench/baselines/training/metrics.py
multabench/baselines/xgboost.py
multabench/benchmark/__init__.py
multabench/benchmark/curation/__init__.py
multabench/benchmark/curation/prepare.py
multabench/benchmark/curation/upload.py
multabench/benchmark/datasets/BIN_IMAGE_CELEB_ATTRACTIVENESS.py
multabench/benchmark/datasets/BIN_IMAGE_HATEFUL_MEME.py
multabench/benchmark/datasets/BIN_IMAGE_MAMMOGRAPHY_CMMD.py
multabench/benchmark/datasets/BIN_TEXT_FAKE_JOB_POSTING.py
multabench/benchmark/datasets/BIN_TEXT_JIGSAW_TOXICITY.py
multabench/benchmark/datasets/BIN_TEXT_KICKSTARTER_FUNDING.py
multabench/benchmark/datasets/MUL_IMAGE_CBIS_DDSM.py
multabench/benchmark/datasets/MUL_IMAGE_CHEXPERT.py
multabench/benchmark/datasets/MUL_IMAGE_CSGO_SKIN_PRICE.py
multabench/benchmark/datasets/MUL_IMAGE_FLOWER_BOUQUETS.py
multabench/benchmark/datasets/MUL_IMAGE_GLAUCOMA_SMDG.py
multabench/benchmark/datasets/MUL_IMAGE_HUBMAP_HPA.py
multabench/benchmark/datasets/MUL_IMAGE_JUSTIN_INSTAGRAM.py
multabench/benchmark/datasets/MUL_IMAGE_PETFINDER.py
multabench/benchmark/datasets/MUL_IMAGE_ZOOSCAN_ZOOPLANKTON.py
multabench/benchmark/datasets/MUL_TEXT_DATA_SCIENTIST_SALARY.py
multabench/benchmark/datasets/MUL_TEXT_MICHELIN_RESTAURANTS.py
multabench/benchmark/datasets/MUL_TEXT_PRODUCT_SENTIMENT.py
multabench/benchmark/datasets/MUL_TEXT_SPOTIFY_GENRES.py
multabench/benchmark/datasets/MUL_TEXT_US_ACCIDENTS.py
multabench/benchmark/datasets/MUL_TEXT_WINE_REVIEW.py
multabench/benchmark/datasets/MUL_TEXT_WOMEN_CLOTHING_REVIEW.py
multabench/benchmark/datasets/REG_IMAGE_AMAZON_BEST_SELLER.py
multabench/benchmark/datasets/REG_IMAGE_AMAZON_PACKAGES.py
multabench/benchmark/datasets/REG_IMAGE_HNM_FASHION.py
multabench/benchmark/datasets/REG_IMAGE_KHAADI_CLOTHES.py
multabench/benchmark/datasets/REG_IMAGE_LETTERBOXD_MOVIES.py
multabench/benchmark/datasets/REG_IMAGE_MANGO_MASS.py
multabench/benchmark/datasets/REG_IMAGE_MKPHOTO_BOTS.py
multabench/benchmark/datasets/REG_IMAGE_PAINTING_PRICE.py
multabench/benchmark/datasets/REG_TEXT_BABIES_PRICES.py
multabench/benchmark/datasets/REG_TEXT_BOOK_PRICE.py
multabench/benchmark/datasets/REG_TEXT_BOOK_READABILITY.py
multabench/benchmark/datasets/REG_TEXT_MERCARI_MARKETPLACE.py
multabench/benchmark/datasets/REG_TEXT_MONTGOMERY_SALARIES.py
multabench/benchmark/datasets/REG_TEXT_ROTTEN_TOMATOES.py
multabench/benchmark/datasets/REG_TEXT_SCIMAGOJR_IMPACT.py
multabench/benchmark/datasets/REG_TEXT_VANCOUVER_SALARIES.py
multabench/benchmark/datasets/REG_TEXT_VIDEO_GAMES_SALES.py
multabench/benchmark/datasets/REG_TEXT_ZOMATO_RESTAURANTS.py
multabench/benchmark/datasets/__init__.py
multabench/benchmark/load.py
multabench/benchmark/utils/__init__.py
multabench/benchmark/utils/constants.py
multabench/benchmark/utils/curation.py
multabench/constants.py
multabench/datasets/__init__.py
multabench/datasets/all_datasets.py
multabench/datasets/annotated/BIN_IMAGE_SOCIAL_TRENDING_BOOKS.py
multabench/datasets/annotated/BIN_TEXT_FINANCIAL_CONSUMER_COMPLAINT.py
multabench/datasets/annotated/BIN_TEXT_PROFESSIONAL_FAKE_JOB_POSTING.py
multabench/datasets/annotated/BIN_TEXT_PROFESSIONAL_KICKSTARTER_FUNDING.py
multabench/datasets/annotated/BIN_TEXT_SOCIAL_IMDB_GENRE_PREDICTION.py
multabench/datasets/annotated/BIN_TEXT_SOCIAL_JIGSAW_TOXICITY.py
multabench/datasets/annotated/BIN_TEXT_TRANSPORTATION_OSHA_ACCIDENT_INJURY_DATA.py
multabench/datasets/annotated/MUL_IMAGE_ARTM_ART_PRICE_DATASET_MOVEMENT.py
multabench/datasets/annotated/MUL_IMAGE_CONSUMER_WALMART_PRODUCT_PRICING.py
multabench/datasets/annotated/MUL_IMAGE_HEALTHCARE_COVID_CHESTXRAY_PNEUMONIA.py
multabench/datasets/annotated/MUL_IMAGE_LEAGUE_OF_LEGENDS_SKIN_CATEGORY.py
multabench/datasets/annotated/MUL_IMAGE_MNIST_HAM1000_CANCER_SKIN_LESIONS.py
multabench/datasets/annotated/MUL_IMAGE_PETFINDER_ADOPTION_SPEED.py
multabench/datasets/annotated/MUL_IMAGE_STARTUP_2023_COMPANY_EMPLOYEE_SIZES.py
multabench/datasets/annotated/MUL_IMAGE_TOKOPEDIA_PRODUCTS_WEIGHT_ESTIMATION.py
multabench/datasets/annotated/MUL_TEXT_CONSUMER_PRODUCT_SENTIMENT.py
multabench/datasets/annotated/MUL_TEXT_CONSUMER_WOMEN_ECOMMERCE_CLOTHING_REVIEW.py
multabench/datasets/annotated/MUL_TEXT_FOOD_MICHELIN_GUIDE_RESTAURANTS.py
multabench/datasets/annotated/MUL_TEXT_FOOD_WINE_REVIEW.py
multabench/datasets/annotated/MUL_TEXT_FOOD_YELP_REVIEWS.py
multabench/datasets/annotated/MUL_TEXT_HOUSES_MELBOURNE_AIRBNB.py
multabench/datasets/annotated/MUL_TEXT_PROFESSIONAL_DATA_SCIENTIST_SALARY.py
multabench/datasets/annotated/MUL_TEXT_SOCIAL_GOOGLE_QA_TYPE_REASON.py
multabench/datasets/annotated/MUL_TEXT_SOCIAL_HEARTHSTONE_CARD_GAME_WARCRAFT.py
multabench/datasets/annotated/MUL_TEXT_SOCIAL_NEWS_CHANNEL_CATEGORY.py
multabench/datasets/annotated/MUL_TEXT_SOCIAL_SPOTIFY_GENRES.py
multabench/datasets/annotated/MUL_TEXT_TRANSPORTATION_US_ACCIDENTS_MARCH23.py
multabench/datasets/annotated/REG_IMAGE_AMAZON_BEST_SELLER_PRODUCT_RATINGS.py
multabench/datasets/annotated/REG_IMAGE_DVM_DEEP_VISUAL_MARKETING_CAR_PRICES.py
multabench/datasets/annotated/REG_IMAGE_GOODREADS_BOOKS_RATING.py
multabench/datasets/annotated/REG_IMAGE_HOUSES_AIRBNB_SEATTLE.py
multabench/datasets/annotated/REG_IMAGE_STYLISTIC_PRODUCT_PRICE_RATIO_FLIPKART.py
multabench/datasets/annotated/REG_TEXT_CONSUMER_AMERICAN_EAGLE_PRICES.py
multabench/datasets/annotated/REG_TEXT_CONSUMER_BABIES_R_US_PRICES.py
multabench/datasets/annotated/REG_TEXT_CONSUMER_BIKE_PRICE_BIKEWALE.py
multabench/datasets/annotated/REG_TEXT_CONSUMER_BOOK_PRICE_PREDICTION.py
multabench/datasets/annotated/REG_TEXT_CONSUMER_CAR_PRICE_CARDEKHO.py
multabench/datasets/annotated/REG_TEXT_CONSUMER_JC_PENNEY_PRODUCT_PRICE.py
multabench/datasets/annotated/REG_TEXT_CONSUMER_LAPTOP_INDIAN_PRICES.py
multabench/datasets/annotated/REG_TEXT_CONSUMER_MERCARI_ONLINE_MARKETPLACE.py
multabench/datasets/annotated/REG_TEXT_FOOD_ALCOHOL_WIKILIQ_PRICES.py
multabench/datasets/annotated/REG_TEXT_FOOD_BEER_RATINGS.py
multabench/datasets/annotated/REG_TEXT_FOOD_CHOCOLATE_BAR_RATINGS.py
multabench/datasets/annotated/REG_TEXT_FOOD_COFFEE_REVIEW.py
multabench/datasets/annotated/REG_TEXT_FOOD_RAMEN_RATINGS_2022.py
multabench/datasets/annotated/REG_TEXT_FOOD_WINE_POLISH_MARKET_PRICES.py
multabench/datasets/annotated/REG_TEXT_FOOD_WINE_VIVINO_SPAIN.py
multabench/datasets/annotated/REG_TEXT_FOOD_ZOMATO_RESTAURANTS.py
multabench/datasets/annotated/REG_TEXT_HOUSES_AIRBNB_SEATTLE.py
multabench/datasets/annotated/REG_TEXT_HOUSES_CALIFORNIA_PRICES_2020.py
multabench/datasets/annotated/REG_TEXT_HOUSES_SAN_FRANCISCO_PERMITS_APPLICATIONS.py
multabench/datasets/annotated/REG_TEXT_PROFESSIONAL_COMPANY_EMPLOYEES_SIZE.py
multabench/datasets/annotated/REG_TEXT_PROFESSIONAL_EMPLOYEE_RENUMERATION_VANCOUBER.py
multabench/datasets/annotated/REG_TEXT_PROFESSIONAL_EMPLOYEE_SALARY_MONTGOMERY.py
multabench/datasets/annotated/REG_TEXT_PROFESSIONAL_ML_DS_AI_JOBS_SALARIES.py
multabench/datasets/annotated/REG_TEXT_PROFESSIONAL_SCIMAGOJR_ACADEMIC_IMPACT.py
multabench/datasets/annotated/REG_TEXT_SOCIAL_ANIME_PLANET_RATING.py
multabench/datasets/annotated/REG_TEXT_SOCIAL_BOOKS_GOODREADS.py
multabench/datasets/annotated/REG_TEXT_SOCIAL_BOOK_READABILITY_CLEAR.py
multabench/datasets/annotated/REG_TEXT_SOCIAL_FILMTV_MOVIE_RATING_ITALY.py
multabench/datasets/annotated/REG_TEXT_SOCIAL_KOREAN_DRAMA.py
multabench/datasets/annotated/REG_TEXT_SOCIAL_MOVIES_DATASET_REVENUE.py
multabench/datasets/annotated/REG_TEXT_SOCIAL_MOVIES_ROTTEN_TOMATOES.py
multabench/datasets/annotated/REG_TEXT_SOCIAL_MUSEUMS_US_REVENUES.py
multabench/datasets/annotated/REG_TEXT_SOCIAL_VIDEO_GAMES_SALES.py
multabench/datasets/annotated/REG_TEXT_SPORTS_FIFA22_WAGES.py
multabench/datasets/annotated/REG_TEXT_SPORTS_NBA_DRAFT_VALUE_OVER_REPLACEMENT.py
multabench/datasets/annotated/REG_TEXT_TRANSPORTATION_USED_CAR_MERCEDES_BENZ_ITALY.py
multabench/datasets/annotated/REG_TEXT_TRANSPORTATION_USED_CAR_PAKISTAN.py
multabench/datasets/annotated/REG_TEXT_TRANSPORTATION_USED_CAR_SAUDI_ARABIA.py
multabench/datasets/annotated/__init__.py
multabench/datasets/curation.py
multabench/datasets/curation_mapping.py
multabench/datasets/curation_objects.py
multabench/datasets/description.py
multabench/datasets/downloading.py
multabench/datasets/image_benchmarks.py
multabench/datasets/kaggle_competitions.py
multabench/datasets/multimodal.py
multabench/datasets/objects.py
multabench/datasets/text_benchmarks.py
multabench/datasets/url_datasets/babies_r_us.csv
multabench/datasets/url_datasets/bikewale.csv
multabench/datasets/url_datasets/goodreads.csv
multabench/datasets/url_datasets/rotten_tomatoes.csv
multabench/datasets/url_datasets/salaries.csv
multabench/datasets/url_datasets/scimagojr_2024.csv
multabench/datasets/url_datasets/vancouber.csv
multabench/datasets/utils.py
multabench/dino/__init__.py
multabench/dino/constants.py
multabench/dino/dino_finetune.py
multabench/dino/image_loading.py
multabench/e5/__init__.py
multabench/e5/constants.py
multabench/e5/e5_finetune.py
multabench/finetune/train_args.py
multabench/finetune/utils.py
multabench/leaderboard/__init__.py
multabench/leaderboard/data/__init__.py
multabench/leaderboard/data/benchmark.py
multabench/leaderboard/data/keys.py
multabench/leaderboard/data/loading.py
multabench/leaderboard/data/models.py
multabench/leaderboard/data/toy_results/toy_results.csv
multabench/leaderboard/large_results.py
multabench/leaderboard/main_paper/__init__.py
multabench/leaderboard/main_paper/curation_example.py
multabench/leaderboard/main_paper/encoder_scale.py
multabench/leaderboard/main_paper/leaderboard.py
multabench/leaderboard/main_paper/pca.py
multabench/leaderboard/main_paper/text_pool.py
multabench/leaderboard/metadata/__init__.py
multabench/leaderboard/metadata/multimodal_features.py
multabench/leaderboard/multabench_results.py
multabench/leaderboard/no_pca_results.py
… (truncated)
```

## Detected entry points

- `projects/PROJ-577-multabench-benchmarking-multimodal-tabul/external/MulTaBench/multabench/baselines/benchmarks/evaluate.py`
- `projects/PROJ-577-multabench-benchmarking-multimodal-tabul/external/MulTaBench/benchmark.py`
- `projects/PROJ-577-multabench-benchmarking-multimodal-tabul/external/MulTaBench/multabench/constants.py`
- `projects/PROJ-577-multabench-benchmarking-multimodal-tabul/external/MulTaBench/multabench/baselines/abstract_model.py`
- `projects/PROJ-577-multabench-benchmarking-multimodal-tabul/external/MulTaBench/multabench/baselines/autogluon_mm.py`
- `projects/PROJ-577-multabench-benchmarking-multimodal-tabul/external/MulTaBench/multabench/baselines/catboost.py`
- `projects/PROJ-577-multabench-benchmarking-multimodal-tabul/external/MulTaBench/multabench/baselines/contexttab.py`
- `projects/PROJ-577-multabench-benchmarking-multimodal-tabul/external/MulTaBench/multabench/baselines/lgbm.py`
- `projects/PROJ-577-multabench-benchmarking-multimodal-tabul/external/MulTaBench/multabench/baselines/random_forest.py`
- `projects/PROJ-577-multabench-benchmarking-multimodal-tabul/external/MulTaBench/multabench/baselines/realmlp.py`
- `projects/PROJ-577-multabench-benchmarking-multimodal-tabul/external/MulTaBench/multabench/baselines/tabdpt.py`
- `projects/PROJ-577-multabench-benchmarking-multimodal-tabul/external/MulTaBench/multabench/baselines/tabicl_v2.py`
- `projects/PROJ-577-multabench-benchmarking-multimodal-tabul/external/MulTaBench/multabench/baselines/tabm.py`
- `projects/PROJ-577-multabench-benchmarking-multimodal-tabul/external/MulTaBench/multabench/baselines/tabpfnv2.py`
- `projects/PROJ-577-multabench-benchmarking-multimodal-tabul/external/MulTaBench/multabench/baselines/tabstar_v1.py`

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `MulTaBench` — not re-implementing it.
