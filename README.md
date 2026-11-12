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

Unit tests need no stack. Integration tests run locally against a Semiont stack; see the runbook.

## Docs

- [Local Test Runbook](docs/semiont-integration%20Local%20Test%20Runbook.md)
- [Stage 1 PR Plan](docs/semiont-integration%20Stage%201%20PR%20Plan.md)
- [Stage 1 Implementation Plan](docs/Stage%201%20Implementation%20Plan%20Google%20Drive%20Ingestion%20Pipeline.md)
- [Semiont Connectors Integration Plan](docs/Semiont%20Connectors%20Integration%20Plan.md)

## License

Apache-2.0, matching Semiont.
