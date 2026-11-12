# semiont-integration

Connectors that sync external content sources into [Semiont](https://github.com/The-AI-Alliance/semiont)
knowledge bases. Stage 1 syncs Google Shared Drives, one drive per KB, and runs entity detection on what it uploads.

The `semiont` SDK is pinned to the stack's version. Upgrade both together, never one alone.

## Setup

Needs [uv](https://docs.astral.sh/uv/).

```bash
uv sync --all-extras
cp connector.example.toml connector.toml   # then fill in real drive ids
uv run semiont-integration --version
```

## Checks

The same ones CI runs:

```bash
uv run ruff check
uv run ruff format --check
uv run mypy
uv run pyright
uv run pytest
```

Unit tests need no stack. Integration tests run locally against a Semiont stack.

## License

Apache-2.0, matching Semiont.
