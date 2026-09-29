"""
phistory: seamless argparse execution history.

Import this at the very top of your script:

    import phistory

Behaviour:
- On import, if '--history' is present in sys.argv, prints history for the current
  script and exits.
- Patches argparse's parse_args/parse_known_args so that, on first call, the
  invocation (script name + args) is appended to ~/.python-history/<script>.history
  (excluding the --history flag itself).
"""

from .core import install as _install
import os

# Allow disabling automatic install during import for tests or introspection.
# Set the environment variable PHISTORY_NO_AUTO_INSTALL=1 to suppress auto-hooks.
if os.environ.get("PHISTORY_NO_AUTO_INSTALL") != "1":
    _install()

# phistory/__init__.py  (append to the bottom)
from .yaml_args import (
    load as yaml_args_load,
    derive_params_filename,
    load_yaml_params,
)

# nice namespace: phistory.yaml_args.load
from . import yaml_args  # re-export module for ergonomic `from phistory import yaml_args`

__all__ = [
    # existing…
    "yaml_args",
    "yaml_args_load",
    "derive_params_filename",
    "load_yaml_params",
]
