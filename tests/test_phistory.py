
import importlib
import os
import sys
from pathlib import Path
import pytest


def _reload_phistory_core():
    """Reload phistory.core cleanly, without triggering auto-install on import."""
    if "phistory.core" in sys.modules:
        del sys.modules["phistory.core"]
    if "phistory" in sys.modules:
        del sys.modules["phistory"]
    os.environ["PHISTORY_NO_AUTO_INSTALL"] = "1"
    import phistory.core as core  # type: ignore
    importlib.reload(core)
    return core


def _strip_ts_if_present(line: str) -> str:
    """Return the command part of a history line regardless of timestamp presence."""
    line = line.strip()
    if "\t" in line:
        return line.split("\t", 1)[1]
    return line


def test_records_invocation(tmp_path, monkeypatch):
    # History should land under the tmp HOME
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("PYTHONIOENCODING", "utf-8")
    script_name = "myscript.py"
    monkeypatch.setattr(sys, "argv", [script_name, "--foo", "bar", "baz"])

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--foo")
    parser.add_argument("positional")

    import phistory  # noqa: F401  # installs hooks

    ns = parser.parse_args()
    assert ns.foo == "bar"
    assert ns.positional == "baz"

    hist_file = Path(tmp_path, ".python-history", f"{script_name}.history")
    assert hist_file.exists()
    content = hist_file.read_text(encoding="utf-8").strip().splitlines()
    # The stored line is "<ts>\t<script> --foo bar baz". Compare command part only.
    assert _strip_ts_if_present(content[-1]) == f"{script_name} --foo bar baz"


def test_history_flag_prints_and_exits(tmp_path, monkeypatch, capsys):
    script_name = "runme.py"
    hist_dir = Path(tmp_path, ".python-history")
    hist_dir.mkdir(parents=True, exist_ok=True)
    hist_file = hist_dir / f"{script_name}.history"
    # Legacy format (no timestamps) still supported
    hist_file.write_text(
        f"{script_name} --alpha 1\n{script_name} --beta two three\n",
        encoding="utf-8",
    )

    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(sys, "argv", [script_name, "--history"])

    core = _reload_phistory_core()

    with pytest.raises(SystemExit) as exc:
        core.install()

    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert out.strip().splitlines() == [
        f"{script_name} --alpha 1",
        f"{script_name} --beta two three",
    ]


def test_ignores_history_flag_in_record(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    script_name = "cli.py"
    monkeypatch.setattr(sys, "argv", [script_name])

    # Reset modules so _HISTORY_WRITTEN is fresh
    sys.modules.pop("phistory.core", None)
    sys.modules.pop("phistory", None)
    monkeypatch.delenv("PHISTORY_NO_AUTO_INSTALL", raising=False)

    # 🔑 Also clear the argparse sentinel so a fresh patch is applied.
    import argparse
    if hasattr(argparse.ArgumentParser, "_phistory_patched"):
        delattr(argparse.ArgumentParser, "_phistory_patched")

    parser = argparse.ArgumentParser()
    parser.add_argument("--x")

    import phistory  # noqa: F401  # installs hooks fresh

    # Explicitly include --history in args; phistory must filter it out.
    ns = parser.parse_args(["--history", "--x", "y"])
    assert ns.x == "y"

    hist_path = Path(tmp_path, ".python-history", f"{script_name}.history")
    assert hist_path.exists()
    lines = hist_path.read_text(encoding="utf-8").strip().splitlines()
    assert _strip_ts_if_present(lines[-1]) == f"{script_name} --x y"


def test_history_date_option_prints_timestamps(tmp_path, monkeypatch, capsys):
    script_name = "show.py"
    hist_dir = Path(tmp_path, ".python-history")
    hist_dir.mkdir(parents=True, exist_ok=True)
    hist_file = hist_dir / f"{script_name}.history"
    hist_file.write_text(
        "2024-12-31 23:59:59\tshow.py --a 1\n"
        "2025-01-01 00:00:00\tshow.py --b 2 3\n",
        encoding="utf-8",
    )

    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(sys, "argv", [script_name, "--history", "date"])

    core = _reload_phistory_core()
    with pytest.raises(SystemExit) as exc:
        core.install()
    assert exc.value.code == 0

    out_lines = capsys.readouterr().out.strip().splitlines()
    assert out_lines == [
        "2024-12-31 23:59:59 show.py --a 1",
        "2025-01-01 00:00:00 show.py --b 2 3",
    ]


def test_history_unique_option_dedupes(tmp_path, monkeypatch, capsys):
    script_name = "dedupe.py"
    hist_dir = Path(tmp_path, ".python-history")
    hist_dir.mkdir(parents=True, exist_ok=True)
    hist_file = hist_dir / f"{script_name}.history"
    # Two identical commands with different timestamps + one unique
    hist_file.write_text(
        "2025-01-01 10:00:00\tdedupe.py --x 1\n"
        "2025-01-01 10:05:00\tdedupe.py --x 1\n"
        "2025-01-01 10:10:00\tdedupe.py --y 2\n",
        encoding="utf-8",
    )

    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(sys, "argv", [script_name, "--history", "unique"])

    core = _reload_phistory_core()
    with pytest.raises(SystemExit) as exc:
        core.install()
    assert exc.value.code == 0

    # With 'unique' only, dates are not shown; expect first occurrence only.
    out_lines = capsys.readouterr().out.strip().splitlines()
    assert out_lines == [
        "dedupe.py --x 1",
        "dedupe.py --y 2",
    ]


def test_history_date_unique_together(tmp_path, monkeypatch, capsys):
    script_name = "both.py"
    hist_dir = Path(tmp_path, ".python-history")
    hist_dir.mkdir(parents=True, exist_ok=True)
    hist_file = hist_dir / f"{script_name}.history"
    hist_file.write_text(
        "2025-01-01 10:00:00\tboth.py --x 1\n"
        "2025-01-01 10:05:00\tboth.py --x 1\n"  # duplicate command
        "2025-01-01 10:10:00\tboth.py --y 2\n",
        encoding="utf-8",
    )

    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(sys, "argv", [script_name, "--history", "date", "unique"])

    core = _reload_phistory_core()
    with pytest.raises(SystemExit) as exc:
        core.install()
    assert exc.value.code == 0

    # With 'date unique', include the timestamp of the first occurrence only.
    out_lines = capsys.readouterr().out.strip().splitlines()
    assert out_lines == [
        "2025-01-01 10:00:00 both.py --x 1",
        "2025-01-01 10:10:00 both.py --y 2",
    ]
