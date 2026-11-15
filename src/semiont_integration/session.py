"""Signing the connector in to a knowledge base, and opening a session with it."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import override

import httpx
from semiont.http import DeviceCode, HttpTransport, session_from_kept, sign_in_device
from semiont.session import SemiontSession
from semiont.sign_in_store import SignInStore
from semiont.types import KbTarget

from semiont_integration.config import Mapping

__all__ = ["SIGN_INS_FILE", "LoopbackTransport", "http_client", "kb_target", "open_session"]

# The connector's own sign-ins, apart from the launcher's, so it never touches a person's `semiont login`.
SIGN_INS_FILE = "sign-ins.json"


def _is_localhost(host: str) -> bool:
    return host == "localhost" or host.endswith(".localhost")


class LoopbackTransport(httpx.AsyncBaseTransport):
    """Sends `localhost` and `*.localhost` to 127.0.0.1 itself; every other host as usual.

    Such names are loopback by rule (RFC 6761), but macOS's resolver answers
    nothing for `keycloak.localhost`, the issuer a local Docker stack advertises.
    The launcher dials these names at loopback for the same reason. The Host
    header keeps the name, so Keycloak still sees the issuer it expects.
    """

    def __init__(self, inner: httpx.AsyncBaseTransport | None = None) -> None:
        self._inner = inner or httpx.AsyncHTTPTransport(trust_env=False)

    @override
    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        host = request.url.host
        if _is_localhost(host):
            request.url = request.url.copy_with(host="127.0.0.1")
            request.extensions = {**request.extensions, "sni_hostname": host}
        return await self._inner.handle_async_request(request)

    @override
    async def aclose(self) -> None:
        await self._inner.aclose()


def http_client() -> httpx.AsyncClient:
    """The client every request of a session is made with: the SDK's own settings, over `LoopbackTransport`."""
    return httpx.AsyncClient(timeout=None, trust_env=False, transport=LoopbackTransport())


def kb_target(mapping: Mapping) -> KbTarget:
    """The knowledge base a mapping names, at its gateway."""
    return KbTarget(id=mapping.kb_id, label=mapping.kb_id, endpoint=mapping.endpoint)


def _show(code: DeviceCode) -> None:
    if code.verification_uri_complete:
        # The link carries the code: signing in there approves it, and the code is then used up.
        print(f"Open {code.verification_uri_complete} and sign in to approve (code {code.user_code}, already filled in)", flush=True)
    else:
        print(f"Open {code.verification_uri} and enter {code.user_code}", flush=True)


@asynccontextmanager
async def open_session(mapping: Mapping, state_dir: Path) -> AsyncGenerator[SemiontSession[HttpTransport]]:
    """A session with the mapping's KB, held with `async with`.

    Signs in with the device grant only when nothing is kept for this KB yet,
    printing the code to approve. Delete `<state_dir>/sign-ins.json` to sign in again.
    """
    kb = kb_target(mapping)
    kept = SignInStore(state_dir / SIGN_INS_FILE).entry(kb.id)
    async with http_client() as http:
        if await kept.held() is None:
            await sign_in_device(kb, kept, _show, http=http)
        async with session_from_kept(kb, kept=kept, http=http) as session:
            yield session
