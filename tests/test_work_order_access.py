"""Focused tests for dispatch's access decision."""

import unittest

from src.work_order_access import WorkOrderAccessRequest, WorkOrderAccessService, decide_follow_up


class FollowUpDecisionTest(unittest.TestCase):
    def test_signup_sends_otp_to_requested_phone(self) -> None:
        class RecordingClient:
            def __init__(self) -> None:
                self.calls = []

            def post(self, path, body):
                self.calls.append((path, body))
                return {}

        client = RecordingClient()
        request = WorkOrderAccessRequest(
            email="chenhua@changba.com", name="Morgan Lee", phone="+15551234567",
            code="123456", work_order_id="wo-204", dispatch_status="on_site", photo_count=0,
        )
        WorkOrderAccessService(client).start_signup(request)
        self.assertEqual(("/sms/otp", {"to": request.phone}), client.calls[-1])

    def test_verified_technician_without_photos_is_asked_for_arrival_photo(self) -> None:
        request = WorkOrderAccessRequest(
            email="technician@example.com",
            name="Morgan Lee",
            phone="+15551234567",
            code="123456",
            work_order_id="wo-204",
            dispatch_status="on_site",
            photo_count=0,
        )

        decision = decide_follow_up(request, verified=True)

        self.assertTrue(decision.login_verified)
        self.assertEqual("on_site", decision.dispatch_status)
        self.assertEqual("request_arrival_photo", decision.technician_follow_up)


if __name__ == "__main__":
    unittest.main()
