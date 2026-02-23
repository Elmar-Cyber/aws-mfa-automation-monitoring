# AWS IAM MFA Compliance Automation (EventBridge + Lambda + CloudWatch + SNS)

This project automates detection of **IAM users with console access but without MFA enabled**, and sends an **email alert** when non-compliance is found.

It was built as part of an **AWS Cloud Security Automation Series** and demonstrates an end-to-end detection → monitoring → alerting pipeline.

---

## What this solves (plain language)

Manually checking IAM users for MFA is easy to forget and hard to prove over time.  
This automation runs on a schedule and alerts you when a non-compliant user exists.

---

## Architecture

EventBridge (Scheduled Rule)  
→ Lambda (MFA audit)  
→ CloudWatch Logs (evidence)  
→ Metric Filter (log → metric)  
→ CloudWatch Alarm (threshold)  
→ SNS Topic  
→ Email notification

---

## Repository contents

- `lambda_function.py` — MFA audit Lambda (parses IAM Credential Report)
- `trust-policy.json` — Lambda execution role trust policy
- `mfa-audit-policy.json` — IAM policy for least-privilege execution
- `AWS_AUTOMATION_STEP_BY_STEP.docx` — Full step-by-step documentation (screenshots placeholders included)

---

## How it works

1. EventBridge triggers the Lambda on a schedule
2. Lambda generates/reads the IAM credential report and checks:
   - `password_enabled = true` (console access)
   - `mfa_active = false` (no MFA)
3. If any non-compliant users are found, Lambda logs:

   `MFA CHECK ALERT: Found X IAM users without MFA`

4. A CloudWatch Metric Filter matches the log text (`MFA CHECK ALERT`) and emits a custom metric:
   - Namespace: `SecurityAudit`
   - Metric: `MFAFailures`
5. A CloudWatch Alarm triggers when `MFAFailures >= 1`
6. Alarm publishes to SNS → email is sent

---

## Validation (what to expect)

- Creating a new IAM user **with console access** and **no MFA** should result in:
  - Lambda log entry containing `MFA CHECK ALERT`
  - `SecurityAudit/MFAFailures` metric datapoint (Sum = 1)
  - Alarm state changes to **ALARM**
  - SNS email notification received

**Note:** IAM Credential Reports are not always real-time. New users may not appear immediately until the report refreshes.

---

## Key troubleshooting lessons

- Metric filters must match the **exact** log text (e.g., `MFA CHECK ALERT` vs `MFA CHECK FAIL`)
- Metric filters only create metrics for log events generated **after** the filter is created/updated
- CloudWatch alarms must have `AlarmActions` set (SNS Topic ARN), otherwise no notifications are sent

---

## Future improvements (optional)

- Replace credential-report parsing with direct IAM API checks (real-time)
- Integrate with Security Hub / SIEM
- Add auto-remediation workflow (ticketing or quarantine actions)
- Add separate rules for access keys / key age / root MFA

---

## Author

Elmar Scholten — Cloud Security Automation Series
