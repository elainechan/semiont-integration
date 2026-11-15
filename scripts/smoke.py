"""Smoke test against a running stack (runbook §6.1): upload one note, then run detection on it.

    uv run python scripts/smoke.py [--config connector.toml] [--kb acme-litigation]

Touches only Semiont, never Google. Run by hand; it is not part of the unit tests.
"""

import argparse
import asyncio
import sys
from pathlib import Path

from semiont.transport import PutBinaryRequest
from semiont.types import LinkingJobParams

from semiont_integration.config import ConfigError, load_config
from semiont_integration.session import open_session

ENTITY_TYPES = ["Organization"]


async def smoke(config_path: Path, kb_id: str | None) -> None:
    config = load_config(config_path)
    mapping = config.mapping(kb_id) if kb_id else config.mappings[0]
    print(f"KB {mapping.kb_id} at {mapping.gateway}")
    async with open_session(mapping, config.state_dir) as session:
        client = session.client
        await client.frame.add_entity_types(ENTITY_TYPES)
        created = await client.yield_.resource(
            PutBinaryRequest(
                name="Smoke test",
                file=b"# Smoke\n\nAcme Corp signed with Beta LLC.",
                format="text/markdown",
                storage_uri="file://sources/smoke/hello.md",
            )
        )
        print("created", created.resource_id)
        done = await client.mark.delegate(created.resource_id, LinkingJobParams(motivation="linking", entity_types=ENTITY_TYPES))
        print("detection", done.result)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", type=Path, default=Path("connector.toml"))
    parser.add_argument("--kb", help="kb_id of the mapping to use (default: the first)")
    args = parser.parse_args()
    try:
        asyncio.run(smoke(args.config, args.kb))
    except ConfigError as error:
        sys.exit(str(error))


if __name__ == "__main__":
    main()
