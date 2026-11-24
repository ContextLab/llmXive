#!/usr/bin/env bash
# Remove the platform-owned `state/` shadow directory that a prior
# (dropped) task created inside the project tree. The platform owns
# `state/...`; project code must never write there (see tasks.md,
# "Platform-owned paths" and the T051 drop note).
set -e
cd "$(dirname "$0")/.."
if [ -d state ]; then
    rm -rf state
    echo "[cleanup] removed stale state/ shadow directory"
else
    echo "[cleanup] no state/ shadow directory present"
fi
