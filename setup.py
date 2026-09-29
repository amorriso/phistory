from pathlib import Path
from setuptools import setup, find_packages

version_ns = {}
with open(Path(__file__).parent / "phistory" / "__version__.py", "r", encoding="utf-8") as f:
    exec(f.read(), version_ns)

setup(
    name="phistory",
    version=version_ns["__version__"],
    description="Zero-config argparse history recorder and replayer",
    long_description=Path("README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    author="amorriso",
    license="Unlicense",
    packages=find_packages(exclude=("tests",)),
    python_requires=">=3.13",
    install_requires=["PyYAML>=6.0"],
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
    ],
)

