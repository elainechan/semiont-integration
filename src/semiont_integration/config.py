"""The connector's config file, `connector.toml`."""

import tomllib
from pathlib import Path
from typing import Literal, Self
from urllib.parse import urlsplit

from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator
from semiont.http import is_valid_hostname
from semiont.types import HttpEndpoint

__all__ = ["Config", "ConfigError", "Mapping", "load_config", "parse_gateway"]

_DEFAULT_PORTS = {"http": 80, "https": 443}


class ConfigError(Exception):
    """The config file is missing, is not TOML, or does not have the shape the connector reads."""


def parse_gateway(url: str) -> HttpEndpoint:
    """The endpoint a gateway URL names: `http(s)://host[:port]`, with nothing after the port."""
    parts = urlsplit(url)
    if parts.scheme not in _DEFAULT_PORTS:
        raise ValueError(f"gateway must start with http:// or https://, got {url!r}")
    if parts.path not in ("", "/") or parts.query or parts.fragment or parts.username or parts.password:
        raise ValueError(f"gateway must be only a scheme, host and port, got {url!r}")
    host = parts.hostname or ""
    if not is_valid_hostname(host):
        raise ValueError(f"gateway has no valid host, got {url!r}")
    try:
        port = parts.port or _DEFAULT_PORTS[parts.scheme]
    except ValueError:
        raise ValueError(f"gateway has an invalid port, got {url!r}") from None
    protocol: Literal["http", "https"] = "https" if parts.scheme == "https" else "http"
    return HttpEndpoint(kind="http", host=host, port=port, protocol=protocol)


class Mapping(BaseModel, frozen=True):
    """One knowledge base the connector writes to, and the gateway it is reached at."""

    kb_id: str
    gateway: str

    @field_validator("kb_id")
    @classmethod
    def _kb_id_not_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("kb_id must not be empty")
        return value

    @field_validator("gateway")
    @classmethod
    def _gateway_is_url(cls, value: str) -> str:
        parse_gateway(value)
        return value

    @property
    def endpoint(self) -> HttpEndpoint:
        return parse_gateway(self.gateway)


class Config(BaseModel, frozen=True):
    """What the connector reads from `connector.toml`. Keys later PRs read are ignored for now."""

    state_dir: Path = Path(".state")
    # The file spells each one `[[mapping]]`.
    mappings: tuple[Mapping, ...] = Field(alias="mapping")

    @model_validator(mode="after")
    def _kb_ids_unique(self) -> Self:
        if not self.mappings:
            raise ValueError("at least one [[mapping]] is required")
        seen: set[str] = set()
        for mapping in self.mappings:
            if mapping.kb_id in seen:
                raise ValueError(f"kb_id {mapping.kb_id!r} appears in more than one [[mapping]]")
            seen.add(mapping.kb_id)
        return self

    def mapping(self, kb_id: str) -> Mapping:
        """The mapping for `kb_id`."""
        for mapping in self.mappings:
            if mapping.kb_id == kb_id:
                return mapping
        known = ", ".join(m.kb_id for m in self.mappings)
        raise ConfigError(f"no [[mapping]] has kb_id {kb_id!r} (known: {known})")


def load_config(path: Path) -> Config:
    """Read and check `path`. Every problem is raised as a `ConfigError` naming the file."""
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ConfigError(f"{path}: not found (copy connector.example.toml to start)") from None
    except tomllib.TOMLDecodeError as error:
        raise ConfigError(f"{path}: not valid TOML: {error}") from None
    try:
        return Config.model_validate(data)
    except ValidationError as error:
        problems = "\n".join(f"  {_location(e['loc'])}: {e['msg']}" for e in error.errors())
        raise ConfigError(f"{path}:\n{problems}") from None


def _location(loc: tuple[int | str, ...]) -> str:
    # ("mapping", 0, "gateway") reads as "mapping[0].gateway".
    out = ""
    for part in loc:
        out += f"[{part}]" if isinstance(part, int) else (f".{part}" if out else part)
    return out or "(file)"
