from pathlib import Path

import pytest

from semiont_integration.config import ConfigError, load_config, parse_gateway
from semiont_integration.session import kb_target

EXAMPLE = Path(__file__).parent.parent / "connector.example.toml"


def write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "connector.toml"
    path.write_text(text, encoding="utf-8")
    return path


def test_example_config_loads() -> None:
    config = load_config(EXAMPLE)
    assert config.state_dir == Path(".state")
    assert [m.kb_id for m in config.mappings] == ["acme-litigation", "acme-corporate"]
    assert config.mapping("acme-corporate").endpoint.port == 4001


def test_state_dir_defaults(tmp_path: Path) -> None:
    config = load_config(write(tmp_path, '[[mapping]]\nkb_id = "a"\ngateway = "http://localhost:4000"\n'))
    assert config.state_dir == Path(".state")


def test_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="not found"):
        load_config(tmp_path / "nope.toml")


def test_not_toml(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="not valid TOML"):
        load_config(write(tmp_path, "[[mapping]\n"))


def test_missing_field(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match=r"mapping\[0\]\.gateway: Field required"):
        load_config(write(tmp_path, '[[mapping]]\nkb_id = "a"\n'))


def test_no_mappings(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="mapping: Field required"):
        load_config(write(tmp_path, 'state_dir = ".state"\n'))


def test_bad_url(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match=r"mapping\[0\]\.gateway: .*http:// or https://"):
        load_config(write(tmp_path, '[[mapping]]\nkb_id = "a"\ngateway = "localhost:4000"\n'))


def test_duplicate_kb_ids(tmp_path: Path) -> None:
    text = '[[mapping]]\nkb_id = "a"\ngateway = "http://localhost:4000"\n' * 2
    with pytest.raises(ConfigError, match="'a' appears in more than one"):
        load_config(write(tmp_path, text))


def test_unknown_kb_id() -> None:
    with pytest.raises(ConfigError, match="no \\[\\[mapping\\]\\] has kb_id 'zzz'"):
        load_config(EXAMPLE).mapping("zzz")


@pytest.mark.parametrize(
    ("url", "host", "port", "protocol"),
    [
        ("http://localhost:4000", "localhost", 4000, "http"),
        ("http://localhost:4000/", "localhost", 4000, "http"),
        ("https://kb.example.com", "kb.example.com", 443, "https"),
        ("http://kb.example.com", "kb.example.com", 80, "http"),
    ],
)
def test_parse_gateway(url: str, host: str, port: int, protocol: str) -> None:
    endpoint = parse_gateway(url)
    assert (endpoint.host, endpoint.port, endpoint.protocol) == (host, port, protocol)


@pytest.mark.parametrize(
    "url",
    ["ftp://localhost", "localhost:4000", "http://localhost:4000/api", "http://localhost:99999", "http://user:pw@localhost", "http://"],
)
def test_parse_gateway_refuses(url: str) -> None:
    with pytest.raises(ValueError, match="gateway"):
        parse_gateway(url)


def test_kb_target() -> None:
    mapping = load_config(EXAMPLE).mappings[0]
    kb = kb_target(mapping)
    assert (kb.id, kb.label, kb.endpoint) == ("acme-litigation", "acme-litigation", mapping.endpoint)
