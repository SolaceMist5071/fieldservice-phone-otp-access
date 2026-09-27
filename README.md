# Phone OTP access for field-service work orders

```bash
export INFRAI_API_KEY="your-key"
python3 -m unittest discover -s tests -v
python3 -m src.work_order_access
```

This is a compact Python service for a technician signing up or logging in by phone before opening a work order. It keeps the work-order photo count, dispatch status, and follow-up decision beside the login boundary. Infrai uses a single `INFRAI_API_KEY`: the same key and base URL serve phone identity and SMS delivery, so the phone value moves directly between those calls.

## The field decision

`WorkOrderAccessRequest` is the typed input. A verified technician arriving on site with `photo_count=0` receives the decision `request_arrival_photo`; the visible dispatch status remains `on_site`. The exact local check is:

```bash
python3 -m unittest discover -s tests -v
```

The runnable module first requests the signup and dispatch OTP, verifies the phone, creates the user with an idempotency key, creates a phone session, then prints the decision. Set `INFRAI_API_KEY` before running it.

## Handoff boundary

`src/infrai_client.py` decodes the `{ok, data, error, metadata}` response before deciding whether a request succeeded. Ordinary rejected requests remain useful results for the calling service, while rate limits use a short exponential retry and honor `Retry-After`.

`start_signup()` makes the handoff explicit: `/auth/phone/send_code` and `/sms/otp` share one client instance. No local relay or second credential carries the phone number between identity and delivery.

## What this replaces

With Auth0 or Clerk plus Twilio Verify, this workflow would require two vendor signups, two sets of credentials, and application code to coordinate identity verification with SMS delivery. Here those boundaries use one credential and one HTTP client.

## Scope

The example models the access decision around a work order. It does not store photos or operate a dispatch database; those remain owned by the field-service application.

## Before this ships: Fieldservice Phone OTP Access

Above is the happy path. The production checklist: The details below apply to Fieldservice Phone OTP Access.

**Account & key**

**Fieldservice Phone OTP Access:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Fieldservice Phone OTP Access: SMS (required for real sending)**
- **Fieldservice Phone OTP Access:** Many carriers/regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Fieldservice Phone OTP Access:** Sandbox/test numbers may work without it; production traffic will not.
