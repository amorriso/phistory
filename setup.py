from pathlib import Path

from setuptools import find_packages, setup

ROOT = Path(__file__).parent
version_ns = {}
with open(ROOT / "phistory" / "__version__.py", "r", encoding="utf-8") as f:
    exec(f.read(), version_ns)

setup(
    name="phistory",
    version=version_ns["__version__"],
    description="Per-script argparse command history and YAML configuration",
    long_description=(ROOT / "README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    author="amorriso",
    license="MIT",
    packages=find_packages(exclude=("tests",)),
    python_requires=">=3.10",
    install_requires=["PyYAML>=6.0"],
    include_package_data=True,
    keywords=[
        "argparse",
        "cli",
        "command history",
        "experiment tracking",
        "reproducibility",
        "yaml configuration",
    ],
    project_urls={
        "Homepage": "https://github.com/amorriso/phistory",
        "Source": "https://github.com/amorriso/phistory",
        "Issues": "https://github.com/amorriso/phistory/issues",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
    ],
)
