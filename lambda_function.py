import boto3
import csv
import io
import time
from datetime import datetime

iam = boto3.client("iam")

def _get_credential_report(max_wait_seconds: int = 60) -> bytes:
    # Kick off generation (safe to call repeatedly)
    iam.generate_credential_report()

    # Poll until it's ready
    deadline = time.time() + max_wait_seconds
    last_err = None

    while time.time() < deadline:
        try:
            resp = iam.get_credential_report()
            return resp["Content"]  # bytes
        except iam.exceptions.ReportInProgressException as e:
            last_err = e
            time.sleep(2)
        except iam.exceptions.CredentialReportNotPresentException as e:
            last_err = e
            time.sleep(2)

    raise RuntimeError(f"Timed out waiting for credential report. Last error: {last_err}")

def _parse_no_mfa_users(report_bytes: bytes):
    text = report_bytes.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    no_mfa = []

    for r in reader:
        username = (r.get("user") or "").strip()

        # Skip root row if present
        if username in ("<root_account>", ""):
            continue

        mfa_active = (r.get("mfa_active") or "").strip().lower()
        if mfa_active != "true":
            no_mfa.append({
                "user": username,
                "arn": r.get("arn", ""),
                "password_enabled": r.get("password_enabled", ""),
                "access_key_1_active": r.get("access_key_1_active", ""),
                "access_key_2_active": r.get("access_key_2_active", ""),
            })

    return no_mfa

def lambda_handler(event, context):
    report_bytes = _get_credential_report(max_wait_seconds=90)
    no_mfa = _parse_no_mfa_users(report_bytes)

    ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    if not no_mfa:
        print(f"[{ts}] MFA CHECK OK: No IAM users without MFA found.")
        return {"status": "ok", "no_mfa_users": 0, "users": []}

    print(f"[{ts}] MFA CHECK ALERT: Found {len(no_mfa)} IAM users without MFA:")
    for u in no_mfa:
        print(
            f" - {u['user']} arn={u['arn']} "
            f"pwd={u['password_enabled']} ak1={u['access_key_1_active']} ak2={u['access_key_2_active']}"
        )

    return {"status": "alert", "no_mfa_users": len(no_mfa), "users": no_mfa}

