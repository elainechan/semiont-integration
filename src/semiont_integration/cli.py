"""The `semiont-integration` command."""

import argparse
from collections.abc import Sequence

from semiont_integration import __version__


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="semiont-integration",
        description="Sync external content sources into Semiont knowledge bases.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    parser.parse_args(argv)
    parser.print_help()
