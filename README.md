# phistory

You know a script worked yesterday—but not *how* you ran it. The useful command
is buried in one terminal's scrollback, missing from another terminal's shell
history, or mixed in with hundreds of unrelated commands.

`phistory` fixes that at the script level: each `argparse` script keeps its own
copy/paste-ready run history. It also includes a tiny YAML parameter loader for
the long, experiment-style commands that are easier to review and version
control as configuration files.

It supports Python 3.10+.

Source and issue tracker: <https://github.com/amorriso/phistory>.

---

## Never reconstruct a command again

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

That history belongs to `myscript.py`, not to whichever shell or terminal
happened to run it. Open a new terminal, come back next week, or switch between
projects: `python myscript.py --history` shows the commands that ran *that
script*.

---

## What it does

- Saves each execution’s CLI (`script name + args`) to
  `~/.python-history/<script>.history`.
- When run with `--history`, prints previous runs (copy/paste friendly) and exits.
- Only writes history when your script calls `argparse.parse_args` or `parse_known_args`.
- The `--history` flag itself is never recorded.

**History directory:** `~/.python-history/`

Use `--history date` to include timestamps, `--history unique` to show only
the first occurrence of each command, or both options together.

> `phistory` intentionally monkey-patches `argparse.ArgumentParser` when it is
> imported. Import it before importing or configuring `argparse` in a script
> that should record history.

> Do not pass passwords, API keys, or other secrets as command-line arguments:
> `phistory` deliberately records arguments so commands can be replayed. Use
> environment variables or an ignored local configuration file for secrets.

---

## When the command has too many arguments

For a script with a handful of flags, a command line is great. For a training,
reporting, or batch job with a dozen settings, it is often easier to keep the
run configuration in a YAML file. The configuration is readable and
reviewable. One useful idea: a params file can also be version-controlled with
your script when you want to keep a reproducible record of a run.

For example, instead of remembering this:

```bash
python train_model.py --dataset data/races-2025.parquet --output-dir artifacts/v3 \
  --learning-rate 0.0003 --batch-size 128 --epochs 80 --seed 42 \
  --validation-days 28 --feature-set market-v4 --early-stopping-patience 10 \
  --notes "baseline before feature experiment"
```

write `configs/baseline.params.yaml`:

```yaml
dataset: data/races-2025.parquet
output_dir: artifacts/v3
learning_rate: 0.0003
batch_size: 128
epochs: 80
seed: 42
validation_days: 28
feature_set: market-v4
early_stopping_patience: 10
notes: baseline before feature experiment
```

Then make the script self-documenting:

```python
# train_model.py
from phistory import yaml_args

args = yaml_args.load(required=["dataset", "output_dir", "learning_rate"])
print(args.output_dir)  # YAML keys are available as attributes
```

Run it with:

```bash
python train_model.py configs/baseline.params.yaml
```

You might version-control `configs/baseline.params.yaml` when it represents a
run worth preserving. Keep credentials, API keys, and machine-specific paths
in an ignored local YAML file instead.

### Behavior

- Default file: `<script_stem>.params.yaml` in the current directory (e.g.
  `runner.params.yaml`)
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

## Using an AI coding assistant

If you use an AI coding assistant in a project, add this to that project's
instructions file (for example `AGENTS.md`, `CLAUDE.md`, or Copilot
instructions) to make the convention explicit:

```md
For reusable Python scripts that use argparse, add `import phistory` as the
first import so each script retains a replayable command history. For scripts
with many stable parameters, consider `phistory.yaml_args` and a params YAML
file. Do not use phistory when command-line arguments contain secrets.
```

This is an opt-in convention for scripts people run repeatedly—not a reason to
add a dependency to every one-off program.

---

## Installation

```bash
pip install phistory
```

---

## License

MIT. See [LICENSE](LICENSE).
