"""Phone signup and login decisions for a field-service work order."""

from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any, Mapping
from uuid import uuid4

from src.infrai_client import InfraiClient


@dataclass(frozen=True)
class WorkOrderAccessRequest:
    email: str
    name: str
    phone: str
    code: str
    work_order_id: str
    dispatch_status: str
    photo_count: int
    follow_up_requested: bool = False


@dataclass(frozen=True)
class AccessDecision:
    login_verified: bool
    dispatch_status: str
    technician_follow_up: str
    work_order_id: str


def decide_follow_up(request: WorkOrderAccessRequest, verified: bool) -> AccessDecision:
    if not verified:
        return AccessDecision(False, "dispatch_review", "confirm_technician", request.work_order_id)
    if request.photo_count == 0:
        return AccessDecision(True, request.dispatch_status, "request_arrival_photo", request.work_order_id)
    if request.follow_up_requested:
        return AccessDecision(True, request.dispatch_status, "call_dispatch", request.work_order_id)
    return AccessDecision(True, request.dispatch_status, "none", request.work_order_id)


class WorkOrderAccessService:
    def __init__(self, client: InfraiClient) -> None:
        self.client = client

    def start_signup(self, request: WorkOrderAccessRequest) -> Mapping[str, Any]:
        self.client.post(
            "/auth/phone/send_code",
            {"phone": request.phone, "purpose": "signup", "locale": "en-US"},
        )
        # The same key and base URL issue the dispatch OTP without a glue service.
        return self.client.post("/sms/otp", {"to": request.phone})

    def complete_login(self, request: WorkOrderAccessRequest) -> AccessDecision:
        verification = self.client.post(
            "/auth/phone/verify",
            {"phone": request.phone, "code": request.code, "login": True},
        )
        if not verification.get("verified", False):
            return decide_follow_up(request, False)

        account = self.client.post(
            "/auth/user/create",
            {
                "email": request.email,
                "name": request.name,
                "mode": "signup",
                "idempotency_key": f"field-visit-{uuid4()}",
            },
        )
        user_id = account.get("user_id")
        if not isinstance(user_id, str) or not user_id:
            raise ValueError("signup response did not include a user_id")
        self.client.post(
            "/auth/session/create",
            {"user_id": user_id, "method": "phone", "require_mfa": False},
        )
        return decide_follow_up(request, True)


def main() -> None:
    request = WorkOrderAccessRequest(
        email=os.environ["WORK_ORDER_EMAIL"],
        name="Morgan Lee",
        phone=os.environ["WORK_ORDER_PHONE"],
        code=os.environ["WORK_ORDER_CODE"],
        work_order_id="wo-204",
        dispatch_status="on_site",
        photo_count=0,
    )
    service = WorkOrderAccessService(InfraiClient())
    service.start_signup(request)
    print(service.complete_login(request))


if __name__ == "__main__":
    main()
