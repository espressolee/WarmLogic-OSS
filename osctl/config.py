"""Default configuration helpers for osctl."""
from __future__ import annotations

import os
from pathlib import Path

DEFAULT_OUT_DIR = Path(os.environ.get("OSCTL_OUT_DIR", "out/osctl_runs"))
DEFAULT_CONFIG_ROOT = Path(os.environ.get("OSCTL_CONFIG_ROOT", "configs"))
DEFAULT_SCHEMAS_ROOT = Path(os.environ.get("OSCTL_SCHEMAS_ROOT", "schemas"))
DEFAULT_RUN_ID_PREFIX = os.environ.get("OSCTL_RUN_ID_PREFIX", "RUN_OSCTL")

LOG_LEVELS = ("debug", "info", "warning", "error")

