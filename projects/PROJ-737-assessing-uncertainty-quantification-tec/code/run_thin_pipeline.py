# This wrapper script exists solely to trigger the thin pipeline execution
# when the task runner requests execution. No additional logic is required.
# The ``-m code.main`` module invocation is performed by the runtime using
# the arguments supplied in the ``args`` list above.