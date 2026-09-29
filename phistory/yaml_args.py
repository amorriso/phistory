"""
phistory.yaml_args
Ultra-minimal YAML-based argument loader to complement phistory's zero-config history.

Usage:
    from phistory import yaml_args
    args = yaml_args.load()  # looks in PWD for "<script>.params.yaml"
    # or: args = yaml_args.load("/path/to/params.yaml")

Conventions:
- Default params filename is derived from your script name and searched in the
  current working directory (pwd): "<script_stem>.params.yaml".
- If the user supplies a single positional argument (that does not start with "-"),
  it is treated as the params file path (absolute or relative).
- You can also pass params_file explicitly.

Returns:
- argparse.Namespace by default (attribute access), or a dict with as_namespace=False.
"""

from __future__ import annotations
import os
import re
import sys
from argparse import Namespace
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional

try:
    import yaml  # type: ignore
except Exception as e:  # pragma: no cover
    raise RuntimeError(
        "PyYAML is required for phistory.yaml_args. "
        "Install with: pip install PyYAML"
    ) from e


def derive_params_filename(script_path: Optional[str] = None, suffix: str = ".params.yaml") -> str:
    """
    Derive "<script_stem>.params.yaml" from a script path.
    Example: "/x/run_experiment.py" -> "run_experiment.params.yaml"
    """
    if not script_path:
        script_path = sys.argv[0] or "script.py"
    stem = re.sub(r"\.py$", "", os.path.basename(script_path))
    return f"{stem}{suffix}"


def load_yaml_params(params_filename: str) -> Dict[str, Any]:
    """
    Load YAML from disk.
    - Raises FileNotFoundError if the file does not exist.
    - Returns {} if the YAML is empty.
    """
    path = Path(params_filename)
    if not path.exists():
        raise FileNotFoundError(f"Parameters file not found: {params_filename}")
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def require_keys(params: Mapping[str, Any], required: Iterable[str]) -> None:
    """Raise ValueError if any required key is missing."""
    missing = [k for k in required if k not in params]
    if missing:
        raise ValueError(f"Missing required parameter(s) in YAML: {', '.join(missing)}")


def _positional_argv_candidate() -> Optional[str]:
    """
    Return the first positional (non-flag) argument from sys.argv (if any).
    Flags start with '-'. Only checks argv[1], in keeping with the "single argument" UX.
    """
    if len(sys.argv) >= 2:
        first = sys.argv[1]
        if first and not first.startswith("-"):
            return first
    return None


def load(
    params_file: Optional[str] = None,
    required: Optional[Iterable[str]] = None,
    *,
    as_namespace: bool = True,
) -> Namespace | Dict[str, Any]:
    """
    Load parameters from YAML with zero script-side config.

    Resolution order:
      1) If params_file is provided, use it.
      2) Else if a single positional (non-flag) argv is present and points to an existing file, use it.
      3) Else look in the current working directory for "<script_stem>.params.yaml".

    Args:
        params_file: optional path to YAML.
        required:    optional iterable of required keys to enforce.
        as_namespace: if True (default) return argparse.Namespace; else a dict.

    Returns:
        argparse.Namespace (default) or dict with the YAML keys as attributes/keys.
    """
    searched: list[str] = []

    # 1) Explicit path wins
    if params_file:
        pf_path = Path(params_file)
        searched.append(str(pf_path))
        if not pf_path.exists():
            raise FileNotFoundError(
                f"Parameters file not found: {pf_path}"
            )
        params = load_yaml_params(str(pf_path))
    else:
        # 2) Single positional argv candidate
        cand = _positional_argv_candidate()
        if cand:
            cand_path = Path(cand)
            searched.append(str(cand_path))
            if cand_path.exists():
                params = load_yaml_params(str(cand_path))
            else:
                # 3) Fall back to default in PWD
                default_name = derive_params_filename(sys.argv[0])
                default_path = Path.cwd() / default_name
                searched.append(str(default_path))
                if not default_path.exists():
                    raise FileNotFoundError(
                        "Could not locate a parameters YAML.\n"
                        f"Tried:\n  - {cand_path}\n  - {default_path}\n\n"
                        "Tips:\n"
                        "  • Put '<script_stem>.params.yaml' in the current working directory, or\n"
                        "  • Provide a single positional argument with the path to the YAML, or\n"
                        "  • Call yaml_args.load(params_file='/path/to/file.yaml')."
                    )
                params = load_yaml_params(str(default_path))
        else:
            # 3) Default in PWD
            default_name = derive_params_filename(sys.argv[0])
            default_path = Path.cwd() / default_name
            searched.append(str(default_path))
            if not default_path.exists():
                raise FileNotFoundError(
                    f"Parameters file not found in current directory: {default_path}\n"
                    "Tips:\n"
                    "  • Put '<script_stem>.params.yaml' in the current working directory, or\n"
                    "  • Provide a single positional argument with the path to the YAML, or\n"
                    "  • Call yaml_args.load(params_file='/path/to/file.yaml')."
                )
            params = load_yaml_params(str(default_path))

    if required:
        require_keys(params, required)

    return Namespace(**params) if as_namespace else params

