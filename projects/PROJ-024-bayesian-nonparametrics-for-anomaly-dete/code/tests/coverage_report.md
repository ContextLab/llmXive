# Coverage Report

**Generated**: 2026-05-03 19:57:24
**Status**: FAILED

## Coverage Summary

- **Total Coverage**: 5.06%
- **Required Threshold**: 80.0%
- **Threshold Met**: No

## Test Results

```
============================= test session starts ==============================
platform darwin -- Python 3.11.12, pytest-8.2.2, pluggy-1.6.0 -- /Users/jmanning/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/.venv/bin/python
cachedir: .pytest_cache
rootdir: /Users/jmanning/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code
configfile: pytest.ini
plugins: cov-5.0.0, timeout-2.3.1, mock-3.14.0, memprof-0.2.0, anyio-4.13.0
timeout: 60.0s
timeout method: signal
timeout func_only: False
collecting ... collected 150 items / 11 errors

==================================== ERRORS ====================================
_________ ERROR collecting tests/contract/test_anomaly_score_schema.py _________
code/tests/contract/test_anomaly_score_schema.py:8: in <module>
    from models.anomaly_score import AnomalyScore
code/models/anomaly_score.py:8: in <module>
    class AnomalyScore:
code/models/anomaly_score.py:27: in AnomalyScore
    component_assignments: Optional[List[int]] = field(default=None)
E   NameError: name 'List' is not defined
____________ ERROR collecting tests/contract/test_config_schema.py _____________
code/tests/contract/test_config_schema.py:9: in <module>
    from models.dp_gmm import DPGMMConfig
code/models/dp_gmm.py:21: in <module>
    from models.anomaly_score import AnomalyScore
code/models/anomaly_score.py:8: in <module>
    class AnomalyScore:
code/models/anomaly_score.py:27: in AnomalyScore
    component_assignments: Optional[List[int]] = field(default=None)
E   NameError: name 'List' is not defined
____________ ERROR collecting tests/contract/test_dp_gmm_schema.py _____________
ImportError while importing test module '/Users/jmanning/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/tests/contract/test_dp_gmm_schema.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
code/.venv/lib/python3.11/site-packages/_pytest/python.py:492: in importtestmodule
    mod = import_path(
code/.venv/lib/python3.11/site-packages/_pytest/pathlib.py:591: in import_path
    importlib.import_module(module_name)
/opt/homebrew/Cellar/python@3.11/3.11.12/Frameworks/Python.framework/Versions/3.11/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
<frozen importlib._bootstrap>:1204: in _gcd_import
    ???
<frozen importlib._bootstrap>:1176: in _find_and_load
    ???
<frozen importlib._bootstrap>:1147: in _find_and_load_unlocked
    ???
<frozen importlib._bootstrap>:690: in _load_unlocked
    ???
code/.venv/lib/python3.11/site-packages/_pytest/assertion/rewrite.py:178: in exec_module
    exec(co, module.__dict__)
code/tests/contract/test_dp_gmm_schema.py:18: in <module>
    from src.models.anomaly_score import AnomalyScore
code/src/models/__init__.py:5: in <module>
    from .dp_gmm import DPGMMConfig, DPGMMModel, ELBOHistory, ClusterAnomalyResult, main
code/src/models/dp_gmm.py:124: in <module>
    import _tkinter
E   ModuleNotFoundError: No module named '_tkinter'
__________ ERROR collecting tests/contract/test_timeseries_schema.py ___________
ImportError while importing test module '/Users/jmanning/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/tests/contract/test_timeseries_schema.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
code/.venv/lib/python3.11/site-packages/_pytest/python.py:492: in importtestmodule
    mod = import_path(
code/.venv/lib/python3.11/site-packages/_pytest/pathlib.py:591: in import_path
    importlib.import_module(module_name)
/opt/homebrew/Cellar/python@3.11/3.11.12/Frameworks/Python.framework/Versions/3.11/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
<frozen importlib._bootstrap>:1204: in _gcd_import
    ???
<frozen importlib._bootstrap>:1176: in _find_and_load
    ???
<frozen importlib._bootstrap>:1147: in _find_and_load_unlocked
    ???
<frozen importlib._bootstrap>:690: in _load_unlocked
    ???
code/.venv/lib/python3.11/site-packages/_pytest/assertion/rewrite.py:178: in exec_module
    exec(co, module.__dict__)
code/tests/contract/test_timeseries_schema.py:9: in <module>
    from models.time_series import TimeSeries, TimeSeriesIterator
code/models/time_series.py:14: in <module>
    from ..utils.streaming import StreamingObservation
E   ImportError: attempted relative import beyond top-level package
________ ERROR collecting tests/integration/test_baseline_comparison.py ________
ImportError while importing test module '/Users/jmanning/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/tests/integration/test_baseline_comparison.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
code/.venv/lib/python3.11/site-packages/_pytest/python.py:492: in importtestmodule
    mod = import_path(
code/.venv/lib/python3.11/site-packages/_pytest/pathlib.py:591: in import_path
    importlib.import_module(module_name)
/opt/homebrew/Cellar/python@3.11/3.11.12/Frameworks/Python.framework/Versions/3.11/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
<frozen importlib._bootstrap>:1204: in _gcd_import
    ???
<frozen importlib._bootstrap>:1176: in _find_and_load
    ???
<frozen importlib._bootstrap>:1147: in _find_and_load_unlocked
    ???
<frozen importlib._bootstrap>:690: in _load_unlocked
    ???
code/.venv/lib/python3.11/site-packages/_pytest/assertion/rewrite.py:178: in exec_module
    exec(co, module.__dict__)
code/tests/integration/test_baseline_comparison.py:54: in <module>
    from src.models.time_series import TimeSeries
code/src/models/__init__.py:5: in <module>
    from .dp_gmm import DPGMMConfig, DPGMMModel, ELBOHistory, ClusterAnomalyResult, main
code/src/models/dp_gmm.py:124: in <module>
    import _tkinter
E   ModuleNotFoundError: No module named '_tkinter'
__________ ERROR collecting tests/integration/test_dpgmm_training.py ___________
ImportError while importing test module '/Users/jmanning/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/tests/integration/test_dpgmm_training.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
code/.venv/lib/python3.11/site-packages/_pytest/python.py:492: in importtestmodule
    mod = import_path(
code/.venv/lib/python3.11/site-packages/_pytest/pathlib.py:591: in import_path
    importlib.import_module(module_name)
/opt/homebrew/Cellar/python@3.11/3.11.12/Frameworks/Python.framework/Versions/3.11/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
<frozen importlib._bootstrap>:1204: in _gcd_import
    ???
<frozen importlib._bootstrap>:1176: in _find_and_load
    ???
<frozen importlib._bootstrap>:1147: in _find_and_load_unlocked
    ???
<frozen importlib._bootstrap>:690: in _load_unlocked
    ???
code/.venv/lib/python3.11/site-packages/_pytest/assertion/rewrite.py:178: in exec_module
    exec(co, module.__dict__)
code/tests/integration/test_dpgmm_training.py:28: in <module>
    from src.models.dpgmm import (
code/src/models/__init__.py:5: in <module>
    from .dp_gmm import DPGMMConfig, DPGMMModel, ELBOHistory, ClusterAnomalyResult, main
code/src/models/dp_gmm.py:124: in <module>
    import _tkinter
E   ModuleNotFoundError: No module named '_tkinter'
_______ ERROR collecting tests/integration/test_threshold_calibration.py _______
code/tests/integration/test_threshold_calibration.py:23: in <module>
    from utils.threshold import (
code/utils/__init__.py:9: in <module>
    from .memory_profiler import MemoryProfiler
code/utils/memory_profiler.py:32: in <module>
    from models.dp_gmm import DPGMMModel, DPGMMConfig
code/models/dp_gmm.py:21: in <module>
    from models.anomaly_score import AnomalyScore
code/models/anomaly_score.py:8: in <module>
    class AnomalyScore:
code/models/anomaly_score.py:27: in AnomalyScore
    component_assignments: Optional[List[int]] = field(default=None)
E   NameError: name 'List' is not defined
____________ ERROR collecting tests/unit/test_dp_gmm_edge_cases.py _____________
ImportError while importing test module '/Users/jmanning/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/tests/unit/test_dp_gmm_edge_cases.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
code/.venv/lib/python3.11/site-packages/_pytest/python.py:492: in importtestmodule
    mod = import_path(
code/.venv/lib/python3.11/site-packages/_pytest/pathlib.py:591: in import_path
    importlib.import_module(module_name)
/opt/homebrew/Cellar/python@3.11/3.11.12/Frameworks/Python.framework/Versions/3.11/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
<frozen importlib._bootstrap>:1204: in _gcd_import
    ???
<frozen importlib._bootstrap>:1176: in _find_and_load
    ???
<frozen importlib._bootstrap>:1147: in _find_and_load_unlocked
    ???
<frozen importlib._bootstrap>:690: in _load_unlocked
    ???
code/.venv/lib/python3.11/site-packages/_pytest/assertion/rewrite.py:178: in exec_module
    exec(co, module.__dict__)
code/tests/unit/test_dp_gmm_edge_cases.py:21: in <module>
    from src.models.dpgmm import DPGMMModel, DPGMMConfig, compute_anomaly_score, compute_anomaly_scores_batch
code/src/models/__init__.py:5: in <module>
    from .dp_gmm import DPGMMConfig, DPGMMModel, ELBOHistory, ClusterAnomalyResult, main
code/src/models/dp_gmm.py:124: in <module>
    import _tkinter
E   ModuleNotFoundError: No module named '_tkinter'
______________ ERROR collecting tests/unit/test_memory_profile.py ______________
ImportError while importing test module '/Users/jmanning/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/tests/unit/test_memory_profile.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
code/.venv/lib/python3.11/site-packages/_pytest/python.py:492: in importtestmodule
    mod = import_path(
code/.venv/lib/python3.11/site-packages/_pytest/pathlib.py:591: in import_path
    importlib.import_module(module_name)
/opt/homebrew/Cellar/python@3.11/3.11.12/Frameworks/Python.framework/Versions/3.11/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
<frozen importlib._bootstrap>:1204: in _gcd_import
    ???
<frozen importlib._bootstrap>:1176: in _find_and_load
    ???
<frozen importlib._bootstrap>:1147: in _find_and_load_unlocked
    ???
<frozen importlib._bootstrap>:690: in _load_unlocked
    ???
code/.venv/lib/python3.11/site-packages/_pytest/assertion/rewrite.py:178: in exec_module
    exec(co, module.__dict__)
code/tests/unit/test_memory_profile.py:26: in <module>
    from src.models.dpgmm import DPGMMModel, DPGMMConfig
code/src/models/__init__.py:5: in <module>
    from .dp_gmm import DPGMMConfig, DPGMMModel, ELBOHistory, ClusterAnomalyResult, main
code/src/models/dp_gmm.py:124: in <module>
    import _tkinter
E   ModuleNotFoundError: No module named '_tkinter'
_____________ ERROR collecting tests/unit/test_streaming_update.py _____________
ImportError while importing test module '/Users/jmanning/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/tests/unit/test_streaming_update.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
code/.venv/lib/python3.11/site-packages/_pytest/python.py:492: in importtestmodule
    mod = import_path(
code/.venv/lib/python3.11/site-packages/_pytest/pathlib.py:591: in import_path
    importlib.import_module(module_name)
/opt/homebrew/Cellar/python@3.11/3.11.12/Frameworks/Python.framework/Versions/3.11/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
<frozen importlib._bootstrap>:1204: in _gcd_import
    ???
<frozen importlib._bootstrap>:1176: in _find_and_load
    ???
<frozen importlib._bootstrap>:1147: in _find_and_load_unlocked
    ???
<frozen importlib._bootstrap>:690: in _load_unlocked
    ???
code/.venv/lib/python3.11/site-packages/_pytest/assertion/rewrite.py:178: in exec_module
    exec(co, module.__dict__)
code/tests/unit/test_streaming_update.py:25: in <module>
    from src.models.dpgmm import DPGMMModel, DPGMMConfig, compute_anomaly_score
code/src/models/__init__.py:5: in <module>
    from .dp_gmm import DPGMMConfig, DPGMMModel, ELBOHistory, ClusterAnomalyResult, main
code/src/models/dp_gmm.py:124: in <module>
    import _tkinter
E   ModuleNotFoundError: No module named '_tkinter'
___________ ERROR collecting tests/unit/test_threshold_edge_cases.py ___________
ImportError while importing test module '/Users/jmanning/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/tests/unit/test_threshold_edge_cases.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
code/.venv/lib/python3.11/site-packages/_pytest/python.py:492: in importtestmodule
    mod = import_path(
code/.venv/lib/python3.11/site-packages/_pytest/pathlib.py:591: in import_path
    importlib.import_module(module_name)
/opt/homebrew/Cellar/python@3.11/3.11.12/Frameworks/Python.framework/Versions/3.11/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
<frozen importlib._bootstrap>:1204: in _gcd_import
    ???
<frozen importlib._bootstrap>:1176: in _find_and_load
    ???
<frozen importlib._bootstrap>:1147: in _find_and_load_unlocked
    ???
<frozen importlib._bootstrap>:690: in _load_unlocked
    ???
code/.venv/lib/python3.11/site-packages/_pytest/assertion/rewrite.py:178: in exec_module
    exec(co, module.__dict__)
code/tests/unit/test_threshold_edge_cases.py:19: in <module>
    from utils.threshold import ThresholdCalibrator, compute_adaptive_threshold
code/src/utils/__init__.py:10: in <module>
    from .memory_profiler import MemoryProfiler
code/src/utils/memory_profiler.py:29: in <module>
    from ..anomaly_score import AnomalyScore
E   ImportError: attempted relative import beyond top-level package

--------- coverage: platform darwin, python 3.11.12-final-0 ----------
Name                                                      Stmts   Miss  Cover   Missing
---------------------------------------------------------------------------------------
code/__init__.py                                              0      0   100%
code/baselines/__init__.py                                    0      0   100%
code/baselines/arima.py                                     109     72    34%   31-36, 51, 70-74, 83-110, 116-120, 134-146, 167-200, 213, 218-244, 248
code/baselines/moving_average.py                            120     74    38%   28-35, 50, 70-79, 84, 88-90, 94-99, 111-113, 117, 131-170, 184-192, 196, 200-201, 214, 219-252, 256
code/data/__init__.py                                         0      0   100%
code/data/synthetic_generator.py                            231    231     0%   26-655
code/download_datasets.py                                   201    201     0%   12-526
code/evaluation/__init__.py                                   0      0   100%
code/evaluation/metrics.py                                  145    111    23%   33, 49, 76-78, 94-97, 113-116, 130-140, 155-163, 183-220, 237-263, 290-312, 329-352, 357-378, 382
code/evaluation/plots.py                                    146    146     0%   7-374
code/evaluation/statistical_tests.py                        165    165     0%   7-487
code/models/__init__.py                                       0      0   100%
code/models/anomaly_score.py                                 29     15    48%   28-78
code/models/dp_gmm.py                                       318    309     3%   24-694
code/models/time_series.py                                   95     89     6%   17-275
code/scripts/__init__.py                                      0      0   100%
code/scripts/benchmark_dp_gmm_performance.py                106    106     0%   11-200
code/scripts/compare_performance.py                          63     63     0%   8-135
code/scripts/compute_anomaly_uncertainty.py                  96     96     0%   15-198
code/scripts/consolidate_source_structure.py                113    113     0%   14-247
code/scripts/create_data_structure.py                        45     45     0%   12-144
code/scripts/create_project_structure.py                     91     91     0%   13-291
code/scripts/download_synthetic_control.py                  101    101     0%   11-167
code/scripts/execute_evaluation_pipeline.py                 309    309     0%   14-621
code/scripts/fix_task_paths.py                               36     36     0%   9-72
code/scripts/generate_checksums.py                           57     57     0%   6-152
code/scripts/generate_data_checksums.py                      67     67     0%   7-142
code/scripts/generate_evaluation_plots.py                   110    110     0%   26-315
code/scripts/generate_state_checksums.py                    164    164     0%   17-392
code/scripts/generate_summary_report.py                     214    214     0%   13-391
code/scripts/init_state_file.py                             202    202     0%   12-333
code/scripts/profile_memory_1000_obs.py                      81     81     0%   12-178
code/scripts/reduce_config.py                               124    124     0%   8-260
code/scripts/restructure_code.py                            119    119     0%   6-226
code/scripts/run_all_contract_tests.py                      181    181     0%   10-341
code/scripts/run_constitution_check.py                       69     69     0%   9-136
code/scripts/scan_credentials.py                             94     94     0%   16-222
code/scripts/setup_linting.py                                38     38     0%   5-83
code/scripts/test_concentration_tuning.py                   118    118     0%   9-232
code/scripts/update_state_checksums.py                       85     85     0%   12-133
code/scripts/validate_quickstart_artifacts.py               219    219     0%   13-451
code/scripts/verify_ci_pipeline.py                          115    115     0%   15-218
code/scripts/verify_config_compliance.py                     94     94     0%   10-200
code/scripts/verify_config_size.py                           33     33     0%   9-88
code/scripts/verify_confusion_matrix.py                      66     66     0%   9-113
code/scripts/verify_constitution_principles.py              237    237     0%   17-471
code/scripts/verify_data_structure.py                        98     98     0%   17-209
code/scripts/verify_dataset_downloads.py                     93     93     0%   15-196
code/scripts/verify_decision_boundary.py                    108    108     0%   12-188
code/scripts/verify_dependency_order.py                     154    154     0%   22-341
code/scripts/verify_directory_structure.py                  106    106     0%   14-185
code/scripts/verify_elbo_logs.py                             72     72     0%   7-132
code/scripts/verify_linting.py                               50     50     0%   5-89
code/scripts/verify_metrics_functions.py                     43     43     0%   9-76
code/scripts/verify_parallel_safety.py                      175    175     0%   17-351
code/scripts/verify_project_structure.py                    144    144     0%   12-278
code/scripts/verify_results_artifacts.py                     92     92     0%   12-244
code/scripts/verify_results_path.py                          65     65     0%   15-102
code/scripts/verify_sample_sizes.py                         184    184     0%   8-354
code/scripts/verify_spec_docs.py                            127    127     0%   12-237
code/scripts/verify_spec_files.py                            67     67     0%   14-145
code/scripts/verify_state_checksums.py                      156    156     0%   13-258
code/scripts/verify_statistical_tests.py                     74     74     0%   6-150
code/scripts/verify_task_paths.py                           111    111     0%   11-249
code/scripts/verify_test_files.py                           133    133     0%   11-299
code/scripts/verify_test_files_t074.py                      149    149     0%   9-250
code/scripts/verify_test_files_t075.py                      118    118     0%   12-232
code/scripts/verify_threshold_tests.py                      135    135     0%   16-247
code/scripts/verify_ttest_bonferroni.py                     158    158     0%   11-288
code/src/__init__.py                                          1      0   100%
code/src/baselines/__init__.py                                3      0   100%
code/src/baselines/arima.py                                 109     72    34%   31-36, 51, 70-74, 83-110, 116-120, 134-146, 167-200, 213, 218-244, 248
code/src/baselines/lstm_ae.py                               361    361     0%   11-763
code/src/baselines/moving_average.py                        120     74    38%   28-35, 50, 70-79, 84, 88-90, 94-99, 111-113, 117, 131-170, 184-192, 196, 200-201, 214, 219-252, 256
code/src/data/__init__.py                                     2      0   100%
code/src/data/download_datasets.py                          154    154     0%   16-406
code/src/data/synthetic_generator.py                        231    175    24%   102, 113, 135-185, 207-242, 261-299, 318-363, 387-419, 447-478, 490-495, 528-576, 589-651, 655
code/src/evaluation/__init__.py                               4      0   100%
code/src/evaluation/metrics.py                              145    111    23%   33, 49, 76-78, 94-97, 113-116, 130-140, 155-163, 183-220, 237-263, 290-312, 329-352, 357-378, 382
code/src/evaluation/plots.py                                146     96    34%   77-92, 112-166, 184-199, 219-263, 285-319, 330-371, 374
code/src/evaluation/statistical_tests.py                    165    126    24%   78-117, 152-160, 199-291, 313-365, 384-426, 436-483, 487
code/src/evaluation/stats.py                                121    121     0%   7-380
code/src/models/__init__.py                                   4      3    25%   6-9
code/src/models/advi_engine.py                              217    217     0%   15-630
code/src/models/anomaly_score.py                             29     29     0%   1-78
code/src/models/dp_gmm.py                                  5591   5475     2%   125-5599
code/src/models/dpgmm.py                                    318    318     0%   12-694
code/src/models/time_series.py                               95     95     0%   8-275
code/src/services/__init__.py                                 3      3     0%   9-12
code/src/services/anomaly_detector.py                        72     72     0%   5-230
code/src/services/threshold_calibrator.py                   203    203     0%   8-467
code/src/utils/__init__.py                                    4      2    50%   11-13
code/src/utils/hyperparameter_counter.py                    154    154     0%   7-330
code/src/utils/memory_profiler.py                           217    204     6%   26-27, 30-468
code/src/utils/runtime_monitor.py                           207    207     0%   10-537
code/src/utils/streaming.py                                 153    153     0%   13-414
code/src/utils/threshold.py                                 223    223     0%   24-641
code/src/utils/time_split.py                                248    248     0%   19-668
code/tests/__init__.py                                        0      0   100%
code/tests/conftest.py                                       37     18    51%   17, 22-33, 42-49, 54-56, 61, 76-77
code/tests/contract/__init__.py                               0      0   100%
code/tests/contract/test_anomaly_detector_schema.py          44     23    48%   31-42, 48-52, 57-73, 78-92
code/tests/contract/test_anomaly_score_schema.py             36     31    14%   10-90
code/tests/contract/test_baseline_schema.py                  44     24    45%   16-18, 22-29, 33-39, 43, 47, 51, 58-59, 63-70, 74, 78, 82, 86-87
code/tests/contract/test_config_schema.py                    50     44    12%   10-99
code/tests/contract/test_dataset_schema.py                   65     46    29%   20-21, 25-26, 30-31, 35-36, 40-46, 50-54, 58-63, 67-73, 81-91, 95-99, 103-116
code/tests/contract/test_dp_gmm_schema.py                    66     57    14%   19-130
code/tests/contract/test_elbo_schema.py                      40     27    32%   12-17, 21-22, 26-35, 39-44, 48-54, 58-64, 69-77, 81-86
code/tests/contract/test_evaluation_results_schema.py        50     34    32%   15-24, 28-37, 41-50, 54-65, 69, 73, 77, 81-83, 87-89, 93-95
code/tests/contract/test_lstm_ae_schema.py                   42     27    36%   15-24, 28-29, 33-34, 38-39, 43-50, 54-59, 64-65, 69-70, 74-75, 79-87
code/tests/contract/test_metrics_schema.py                   72     57    21%   36-73, 78-100, 104-114, 118-133
code/tests/contract/test_state_schema.py                     37     23    38%   14-21, 25-38, 42-44, 48-52, 56-64, 68-80, 84-98
code/tests/contract/test_threshold_calibrator_schema.py      48     25    48%   31-41, 47-51, 56-66, 71-78, 83-91
code/tests/contract/test_threshold_schema.py                 33     21    36%   16-18, 22-26, 30-34, 38-39, 43-50, 54-59, 63-70
code/tests/contract/test_timeseries_schema.py                33     27    18%   11-74
code/tests/integration/__init__.py                            0      0   100%
code/tests/integration/test_baseline_comparison.py          246    229     7%   55-597
code/tests/integration/test_dpgmm_training.py               191    181     5%   35-461
code/tests/integration/test_threshold_calibration.py        156    147     6%   32-406
code/tests/unit/__init__.py                                   0      0   100%
code/tests/unit/test_baseline_edge_cases.py                 126    100    21%   28-38, 42-51, 55-67, 71-83, 87-101, 105-115, 123-133, 137-145, 149-157, 161-172, 176-187, 191-199, 204-216, 220-230, 234-239, 243
code/tests/unit/test_baseline_scoring.py                    125    105    16%   29-42, 47-80, 84-117, 125-133, 137-163, 167-195, 199-215, 223-243, 247-278
code/tests/unit/test_dp_gmm_edge_cases.py                   242    235     3%   22-528
code/tests/unit/test_evaluation_edge_cases.py               174    139    20%   31-37, 41-47, 51-57, 61-67, 71-77, 81-85, 89-93, 97-101, 105-109, 113-117, 121-125, 129-133, 137-141, 145-149, 153-158, 162-167, 171-176, 180-187, 191-198, 202-209, 213-222, 226-233, 237-243, 247-255, 259-270, 274-286, 290
code/tests/unit/test_memory_profile.py                      167    160     4%   27-482
code/tests/unit/test_streaming_update.py                    144    135     6%   26-367
code/tests/unit/test_synthetic_data_edge_cases.py           135    104    23%   32-39, 43-50, 54-61, 65-74, 78-87, 91-99, 103-110, 114-128, 132-145, 149-163, 167-180, 184-196, 200-212, 216-228, 232-249, 253-270, 274-289, 293-312, 316-335, 339-361, 365-380, 384-397, 401
code/tests/unit/test_threshold_edge_cases.py                 97     90     7%   22-240
code/utils/__init__.py                                        4      1    75%   11
code/utils/checksum_manager.py                              180    144    20%   56-57, 69-73, 85-94, 98, 102-108, 121-149, 157-173, 185-192, 208-218, 227-248, 257-296, 300-330, 334-369, 372
code/utils/hyperparameter_counter.py                        110    110     0%   7-295
code/utils/memory_profiler.py                               138    125     9%   26-28, 33-313
code/utils/runtime_monitor.py                               164    164     0%   20-393
code/utils/streaming.py                                     153    112    27%   37-40, 44, 54, 92-102, 116-145, 158-162, 166-170, 182-205, 209-218, 230-231, 240, 249, 258, 267-269, 282-287, 291, 295, 299, 320-324, 333-335, 344-347, 351, 355, 367-372, 376-378, 382, 399-412
code/utils/temporal_split.py                                131    131     0%   12-402
code/utils/threshold.py                                     124    124     0%   7-376
---------------------------------------------------------------------------------------
TOTAL                                                     20422  19388     5%
Coverage HTML written to dir code/tests/htmlcov
Coverage XML written to file code/tests/coverage.xml
Coverage JSON written to file code/tests/coverage.json

=========================== short test summary info ============================
ERROR code/tests/contract/test_anomaly_score_schema.py - NameError: name 'List' is not defined
ERROR code/tests/contract/test_config_schema.py - NameError: name 'List' is not defined
ERROR code/tests/contract/test_dp_gmm_schema.py
ERROR code/tests/contract/test_timeseries_schema.py
ERROR code/tests/integration/test_baseline_comparison.py
ERROR code/tests/integration/test_dpgmm_training.py
ERROR code/tests/integration/test_threshold_calibration.py - NameError: name 'List' is not defined
ERROR code/tests/unit/test_dp_gmm_edge_cases.py
ERROR code/tests/unit/test_memory_profile.py
ERROR code/tests/unit/test_streaming_update.py
ERROR code/tests/unit/test_threshold_edge_cases.py
!!!!!!!!!!!!!!!!!!! Interrupted: 11 errors during collection !!!!!!!!!!!!!!!!!!!
============================== 11 errors in 8.06s ==============================

/Users/jmanning/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/.venv/lib/python3.11/site-packages/coverage/report_core.py:107: CoverageWarning: Couldn't parse Python file '/Users/jmanning/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/scripts/run_contract_tests.py' (couldnt-parse); see https://coverage.readthedocs.io/en/7.13.5/messages.html#warning-couldnt-parse
  coverage._warn(msg, slug="couldnt-parse")
/Users/jmanning/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/.venv/lib/python3.11/site-packages/coverage/report_core.py:107: CoverageWarning: Couldn't parse Python file '/Users/jmanning/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/scripts/test_advi_inference.py' (couldnt-parse); see https://coverage.readthedocs.io/en/7.13.5/messages.html#warning-couldnt-parse
  coverage._warn(msg, slug="couldnt-parse")
/Users/jmanning/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/.venv/lib/python3.11/site-packages/coverage/report_core.py:107: CoverageWarning: Couldn't parse Python file '/Users/jmanning/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/scripts/test_missing_value_handling.py' (couldnt-parse); see https://coverage.readthedocs.io/en/7.13.5/messages.html#warning-couldnt-parse
  coverage._warn(msg, slug="couldnt-parse")

```

## Coverage Artifacts

- HTML Report: `code/tests/htmlcov/index.html`
- XML Report: `code/tests/coverage.xml`
- JSON Report: `code/tests/coverage.json`
- This Report: `code/tests/coverage_report.md`

## Verification Commands

```bash
# View HTML report in browser
open code/tests/htmlcov/index.html

# Check XML coverage
cat code/tests/coverage.xml

# Re-run coverage test
python code/scripts/verify_coverage.py
```