# tests/test_yaml_args.py
from pathlib import Path
from phistory import yaml_args, derive_params_filename, load_yaml_params
import pytest

def test_derive_params_filename():
    assert yaml_args.derive_params_filename("/x/run.py") == "run.params.yaml"
    assert derive_params_filename("/x/runner.py") == "runner.params.yaml"

def test_load_yaml_and_required(tmp_path: Path, monkeypatch):
    # Prepare a params file in a temp PWD
    pf = tmp_path / "runner.params.yaml"
    pf.write_text("outpath: out\ndescription: d\nexperiment-name: e\n", encoding="utf-8")

    # Make PWD be tmp_path so default discovery works (searches PWD)
    monkeypatch.chdir(tmp_path)

    # default discovery uses sys.argv[0] to derive name, but file is in PWD
    monkeypatch.setenv("PYTHONIOENCODING", "utf-8")
    monkeypatch.setattr("sys.argv", ["runner.py"])

    args = yaml_args.load()
    assert args.outpath == "out"

    # required OK
    yaml_args.load(required=["experiment-name", "outpath", "description"])

    # missing required key should raise
    pf.write_text("outpath: out\n", encoding="utf-8")
    with pytest.raises(ValueError):
        yaml_args.load(required=["experiment-name"])

def test_single_positional_argument_path(tmp_path: Path, monkeypatch):
    # Create a YAML in a non-PWD directory
    custom = tmp_path / "custom.yaml"
    custom.write_text("alpha: 42\nbeta: true\n", encoding="utf-8")

    # Keep current PWD as-is; pass the path as the single positional arg
    monkeypatch.setattr("sys.argv", ["runner.py", str(custom)])

    args = yaml_args.load()
    assert args.alpha == 42
    assert args.beta is True

