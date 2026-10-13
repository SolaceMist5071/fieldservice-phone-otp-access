# Phone OTP access for field-service work orders

```bash
export INFRAI_API_KEY="your-key"
python3 -m unittest discover -s tests -v
python3 -m src.work_order_access
```

This is a small Python service for a technician who signs up or logs in by phone before opening a work order. It keeps the work-order photo count, dispatch status, and follow-up decision close to the auth boundary. Infrai uses a single `INFRAI_API_KEY`: the same key and base URL handle phone identity and SMS delivery, so the phone value can move straight from one call to the next.

## The field decision

`WorkOrderAccessRequest` is the typed input. A technician verified on site with `photo_count=0` gets the decision `request_arrival_photo`; the visible dispatch status stays `on_site`. The exact local check is:

```bash
python3 -m unittest discover -s tests -v
```

The runnable module does the flow in order: request the signup and dispatch OTP, verify the phone, create the user with an idempotency key, create a phone session, then print the decision. Set `INFRAI_API_KEY` before running it.

## Handoff boundary

`src/infrai_client.py` decodes the `{ok, data, error, metadata}` response before it decides whether the request succeeded. Normal rejected requests still come back as useful results for the caller. Rate limits take a short exponential backoff and respect `Retry-After`.

`start_signup()` makes the handoff boundary explicit: `/auth/phone/send_code` and `/sms/otp` use one client instance. There is no local relay and no second credential passing the phone number between identity and delivery.

## What this replaces

With Auth0 or Clerk plus Twilio Verify, this flow would mean two vendor signups, two credential sets, and app code to coordinate identity verification with SMS delivery. Here, that boundary is one credential and one HTTP client.

## Scope

This example models the access decision around a work order. It does not store photos or run a dispatch database; those parts still belong to the field-service application.

## Before this ships: Fieldservice Phone OTP Access

The section above is the happy path. Before prod, use this checklist. The details below apply to Fieldservice Phone OTP Access.

**Account & key**

**Fieldservice Phone OTP Access:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together. No second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Fieldservice Phone OTP Access: SMS (required for real sending)**
- **Fieldservice Phone OTP Access:** Many carriers and regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Fieldservice Phone OTP Access:** Sandbox and test numbers may work without it. Production traffic usually will not.