import os
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./test_medikiosk.db"

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402
from app.seed import seed  # noqa: E402


def auth(client: TestClient, email: str, password: str = "DemoPass123!") -> dict:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_end_to_end_clinical_flow() -> None:
    Path("test_medikiosk.db").unlink(missing_ok=True)
    with TestClient(app) as client:
        seed()
        assert client.get("/health").status_code == 200
        patients = client.get("/api/v1/kiosk/demo-patients").json()
        session = client.post("/api/v1/kiosk/identify", json={"patient_id": patients[1]["id"], "language": "hi"}).json()
        kiosk_headers = {"X-Kiosk-Session": session["kiosk_token"]}
        assert client.post("/api/v1/kiosk/consent", headers=kiosk_headers, json={"agreed": True}).status_code == 200
        while True:
            current = client.get("/api/v1/kiosk/interview/current", headers=kiosk_headers).json()
            if current["complete"]:
                break
            question = current["question"]
            answers = {"chief_complaint": "Chest pain", "chest_duration": "Today", "chest_severity": "Severe", "breathing_difficulty": "Severe", "medical_history": "No", "allergies": "No"}
            response = client.post("/api/v1/kiosk/interview/answer", headers=kiosk_headers, json={"question_id": question["id"], "answer": answers[question["id"]], "input_method": "touch"})
            assert response.status_code == 200
        assert client.post("/api/v1/kiosk/complete", headers=kiosk_headers).status_code == 200
        staff = auth(client, "staff@medikiosk.local")
        flags = client.get("/api/v1/red-flags", headers=staff).json()
        assert any(item["encounter_id"] == session["encounter_id"] for item in flags)
        new_flag = next(item for item in flags if item["encounter_id"] == session["encounter_id"])
        assert client.patch(f"/api/v1/red-flags/{new_flag['id']}", headers=staff, json={"status": "ACKNOWLEDGED"}).status_code == 200
        doctor = auth(client, "doctor@medikiosk.local")
        summary = client.get(f"/api/v1/encounters/{session['encounter_id']}/summary", headers=doctor)
        assert summary.status_code == 200
        assert client.post(f"/api/v1/encounters/{session['encounter_id']}/summary/verify", headers=doctor).json()["verification_status"] == "VERIFIED"
        assert client.get(f"/api/v1/encounters/{session['encounter_id']}/fhir", headers=doctor).json()["resourceType"] == "Bundle"


def test_rbac_blocks_staff_verification() -> None:
    with TestClient(app) as client:
        seed()

        doctor = auth(client, "doctor@medikiosk.local")
        staff = auth(client, "staff@medikiosk.local")

        encounters_response = client.get(
            "/api/v1/encounters",
            headers=doctor,
        )

        assert encounters_response.status_code == 200
        encounter = encounters_response.json()[0]

        response = client.post(
            f"/api/v1/encounters/{encounter['id']}/summary/verify",
            headers=staff,
        )

        assert response.status_code == 403