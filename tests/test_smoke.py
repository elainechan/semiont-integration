import importlib
from importlib.metadata import version

import pytest

import semiont_integration
from semiont_integration.cli import main

# Keep in step with the pin in pyproject.toml: a drifting lockfile fails here.
SEMIONT_VERSION = "0.7.2"


def test_package_imports() -> None:
    assert semiont_integration.__version__ == "0.1.0"


def test_semiont_is_pinned_version() -> None:
    importlib.import_module("semiont")
    assert version("semiont") == SEMIONT_VERSION


def test_cli_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["--version"])
    assert exit_info.value.code == 0
    assert capsys.readouterr().out.strip() == "0.1.0"
