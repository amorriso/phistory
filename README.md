# phistory

`phistory` makes Python scripts remember how they were run, and provides a
small YAML parameter loader for scripts that do not use `argparse`.

It supports Python 3.10+.

---

## Quickstart

```python
# myscript.py
import phistory  # must be first
import argparse

p = argparse.ArgumentParser()
p.add_argument("--foo")
p.add_argument("bar")
args = p.parse_args()
print(args)
```

### Run

```bash
python myscript.py --foo 123 hello
python myscript.py --foo 999 world
python myscript.py --history
# outputs:
# myscript.py --foo 123 hello
# myscript.py --foo 999 world
```

---

## What it does

- Saves each execution’s CLI (`script name + args`) to `~/.python-history/<script>.history`.
- When run with `--history`, prints previous runs (copy/paste friendly) and exits.
- Only writes history when your script calls `argparse.parse_args` or `parse_known_args`.
- The `--history` flag itself is never recorded.

**History directory:** `~/.python-history/`

Use `--history date` to include timestamps, `--history unique` to show only
the first occurrence of each command, or both options together.

> `phistory` intentionally monkey-patches `argparse.ArgumentParser` when it is
> imported. Import it before importing or configuring `argparse` in a script
> that should record history.

---

## YAML args (no argparse required)

Skip `argparse` entirely and just load parameters from YAML.

```python
from phistory import yaml_args

args = yaml_args.load()  # looks for "<script>.params.yaml" in the current directory
print(args.outpath)      # access fields as attributes
```

### Behavior

- Default file: `<script_stem>.params.yaml` (e.g. `runner.params.yaml`)
- You can also provide the path explicitly or as a single argument:
  ```bash
  python runner.py configs/myexp.yaml
  ```
- Validate required keys:
  ```python
  args = yaml_args.load(required=["experiment-name", "outpath", "description"])
  ```

### Helper functions

```python
from phistory import derive_params_filename, load_yaml_params
```

---

## Installation

```bash
pip install phistory
```

---

## License

MIT. See [LICENSE](LICENSE).
