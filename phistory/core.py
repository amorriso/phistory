import argparse
import os
import sys
import shlex
import subprocess
from pathlib import Path
from typing import Iterable, Optional, Tuple
from datetime import datetime

# Guard to avoid writing multiple times per process execution.
_HISTORY_WRITTEN = False

# Valid suboptions that may follow --history
_HISTORY_SUBOPTS = {"date", "unique"}


def _history_dir() -> Path:
    """
    Compute the history directory dynamically each time so changes to HOME
    are respected. On Windows, prefer LOCALAPPDATA (then APPDATA).
    - Windows: %LOCALAPPDATA%/Python/phistory/history
    - Others : ~/.python-history
    """
    if os.name == "nt":
        base = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA")
        if base:
            return Path(base) / "Python" / "phistory" / "history"
        # Fallback if env vars are missing
        return Path.home() / "AppData" / "Local" / "Python" / "phistory" / "history"
    # POSIX default
    return Path.home() / ".python-history"


def _script_name() -> str:
    # Fall back to "script" if argv[0] is empty.
    return os.path.basename(sys.argv[0]) or "script"


def _history_file_for(script_name: Optional[str] = None) -> Path:
    if script_name is None:
        script_name = _script_name()
    return _history_dir() / f"{script_name}.history"


def _ensure_dir():
    _history_dir().mkdir(parents=True, exist_ok=True)


def _parse_history_options(argv: Iterable[str]) -> Tuple[bool, bool]:
    """
    Scan argv for --history and its optional suboptions.
    Returns: (want_date, want_unique).
    """
    want_date = False
    want_unique = False
    tokens = list(argv)
    for i, tok in enumerate(tokens):
        if tok == "--history":
            # Consume following suboptions while valid (order agnostic)
            j = i + 1
            while j < len(tokens) and tokens[j] in _HISTORY_SUBOPTS:
                if tokens[j] == "date":
                    want_date = True
                elif tokens[j] == "unique":
                    want_unique = True
                j += 1
            break
    return want_date, want_unique


def _filter_args(argv: Iterable[str]) -> list[str]:
    """
    Remove --history and its recognized suboptions from the provided argv.
    Leave everything else intact.
    """
    filtered = []
    it = iter(list(argv))
    for a in it:
        if a == "--history":
            # Skip any recognized suboptions that immediately follow (max two)
            consumed = 0
            while consumed < 2:
                try:
                    nxt = next(it)
                except StopIteration:
                    break
                if nxt in _HISTORY_SUBOPTS:
                    consumed += 1
                    continue
                # Not a recognized suboption: push back into filtered
                filtered.append(nxt)
                break
            continue
        filtered.append(a)
    return filtered


def _join_args_for_shell(args: list[str]) -> str:
    """
    Platform-appropriate quoting for replayable commands.
    - Windows: use subprocess.list2cmdline (CreateProcess/CommandLineToArgvW rules)
    - POSIX  : use shlex.quote
    """
    if os.name == "nt":
        return subprocess.list2cmdline(args)
    return " ".join(shlex.quote(a) for a in args)


def _record_invocation(argv: Optional[Iterable[str]] = None):
    """
    Append a single line to the history file.
    Stored format: "<ISO_DATETIME>\t<commandline>"
    ISO datetime uses seconds precision in local time.
    """
    global _HISTORY_WRITTEN
    if _HISTORY_WRITTEN:
        return
    if argv is None:
        argv = sys.argv[1:]

    args_list = list(argv)
    args_list = _filter_args(args_list)

    # Compose a fully copy/paste-able command line: "<script> <args...>"
    command = _script_name()
    if args_list:
        command += " " + _join_args_for_shell(args_list)

    _ensure_dir()
    hf = _history_file_for()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with hf.open("a", encoding="utf-8") as f:
        f.write(f"{ts}\t{command}\n")

    _HISTORY_WRITTEN = True


def _render_history_line(raw_line: str, want_date: bool) -> Optional[str]:
    """
    Render one history line for output depending on want_date.
    History lines may be either:
      1) "<ts>\t<command>" (new format), or
      2) "<command>" (legacy format)
    Returns the printable string, or None if the line is empty.
    """
    line = raw_line.rstrip("\n")
    if not line:
        return None
    if "\t" in line:
        ts, cmd = line.split("\t", 1)
        return f"{ts} {cmd}" if want_date else cmd
    # legacy format (no timestamp)
    return line if not want_date else line  # no ts to show; print command only


def _print_history_and_exit():
    want_date, want_unique = _parse_history_options(sys.argv[1:])
    hf = _history_file_for()
    seen = set()
    output = []

    if hf.exists():
        with hf.open("r", encoding="utf-8") as f:
            for raw in f:
                # For uniqueness, dedupe by the *command* part (strip timestamp if present)
                dedupe_key = raw.split("\t", 1)[-1].rstrip("\n")
                if want_unique:
                    if dedupe_key in seen:
                        continue
                    seen.add(dedupe_key)
                rendered = _render_history_line(raw, want_date=want_date)
                if rendered is not None:
                    output.append(rendered)

    if output:
        sys.stdout.write("\n".join(output) + "\n")
    else:
        # No history yet; keep output friendly but still copyable (empty)
        sys.stdout.write("")
    raise SystemExit(0)


def _check_and_handle_history_flag():
    if "--history" in sys.argv[1:]:
        _print_history_and_exit()


def _patch_argparse():
    """Monkey-patch argparse to record once per process when parse_* is called."""
    # Only patch once
    if getattr(argparse.ArgumentParser, "_phistory_patched", False):
        return

    _orig_parse_args = argparse.ArgumentParser.parse_args
    _orig_parse_known_args = argparse.ArgumentParser.parse_known_args

    def _wrap_parse_args(self, args=None, namespace=None):
        # Normalize incoming args (explicit or sys.argv) and strip --history so argparse won't error.
        incoming = list(args) if args is not None else list(sys.argv[1:])
        filtered = _filter_args(incoming)
        # If args is None, pass None so argparse reads from sys.argv; we still record using filtered.
        result = _orig_parse_args(self, args=filtered if args is not None else None, namespace=namespace)
        _record_invocation(filtered)
        return result

    def _wrap_parse_known_args(self, args=None, namespace=None):
        incoming = list(args) if args is not None else list(sys.argv[1:])
        filtered = _filter_args(incoming)
        result = _orig_parse_known_args(self, args=filtered if args is not None else None, namespace=namespace)
        _record_invocation(filtered)
        return result

    argparse.ArgumentParser.parse_args = _wrap_parse_args
    argparse.ArgumentParser.parse_known_args = _wrap_parse_known_args
    argparse.ArgumentParser._phistory_patched = True  # sentinel


def install():
    """
    Entry point called by package import.
    - If '--history' present, print history (with options) and exit.
    - Otherwise patch argparse to record on first parse.
    """
    _check_and_handle_history_flag()
    _patch_argparse()
