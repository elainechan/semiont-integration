import httpx
import pytest

from semiont_integration.session import LoopbackTransport


def recording_client() -> tuple[httpx.AsyncClient, list[httpx.Request]]:
    seen: list[httpx.Request] = []

    def answer(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200)

    return httpx.AsyncClient(transport=LoopbackTransport(httpx.MockTransport(answer))), seen


@pytest.mark.parametrize("url", ["http://keycloak.localhost:8080/realms/x", "http://localhost:4000/api"])
async def test_localhost_names_go_to_loopback(url: str) -> None:
    client, seen = recording_client()
    async with client:
        await client.get(url)
    original = httpx.URL(url)
    assert seen[0].url.host == "127.0.0.1"
    assert seen[0].url.port == original.port
    assert seen[0].url.path == original.path
    assert seen[0].headers["host"] == f"{original.host}:{original.port}"


async def test_other_hosts_untouched() -> None:
    client, seen = recording_client()
    async with client:
        await client.get("https://kb.example.com/api")
    assert seen[0].url.host == "kb.example.com"
    assert "sni_hostname" not in seen[0].extensions
