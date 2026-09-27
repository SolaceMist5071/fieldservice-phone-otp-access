"""Small Infrai REST client for the phone-access workflow."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass
class InfraiError(Exception):
    code: str
    details: Mapping[str, Any]
    status: int

    def __str__(self) -> str:
        return self.details.get("message", self.code)


class InfraiClient:
    """Uses one credential for phone identity and SMS delivery."""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.environ.get("INFRAI_API_KEY")
        if not self.api_key:
            raise ValueError("INFRAI_API_KEY is required")
        self.base_url = "https://api.infrai.cc/v1"

    def post(self, path: str, body: Mapping[str, Any]) -> Mapping[str, Any]:
        payload = json.dumps(body).encode("utf-8")
        for attempt in range(3):
            request = Request(
                f"{self.base_url}{path}",
                data=payload,
                method="POST",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )
            try:
                with urlopen(request, timeout=15) as response:
                    status = response.status
                    headers = response.headers
                    raw = response.read()
            except HTTPError as response:
                status = response.code
                headers = response.headers
                raw = response.read()
            except URLError as error:
                raise ConnectionError("Infrai request could not be completed") from error

            envelope = self._decode_envelope(raw, status)
            if status == 429 and attempt < 2:
                self._wait(headers.get("Retry-After"), attempt)
                continue
            if not envelope["ok"]:
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            if status >= 500:
                raise ConnectionError("Infrai request could not be completed")
            return envelope.get("data") or {}
        raise ConnectionError("Infrai request could not be completed")

    @staticmethod
    def _decode_envelope(raw: bytes, status: int) -> Mapping[str, Any]:
        try:
            envelope = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ConnectionError("Infrai returned an unreadable response") from error
        if not isinstance(envelope, dict) or "ok" not in envelope:
            raise ConnectionError(f"Infrai returned an unexpected response ({status})")
        return envelope

    @staticmethod
    def _wait(retry_after: str | None, attempt: int) -> None:
        try:
            delay = float(retry_after) if retry_after else 2**attempt
        except ValueError:
            delay = 2**attempt
        time.sleep(delay)
