# Verification Report

Package version: `1.0.0`

## Local verification

The following checks were executed during package creation:

```text
python -m compileall -q gate executor scripts tests
python -m unittest discover -s tests -v
python scripts/check_compatibility.py schemas/agent-task-1.0.0.json schemas/agent-task-1.1.0.json
python scripts/check_compatibility.py schemas/agent-task-1.0.0.json schemas/agent-task-2.0.0.json
```

Observed outcomes:

- Python compilation: pass
- Unit tests: 9 of 9 pass
- Version 1.1.0: `COMPATIBLE`
- Version 2.0.0: `BREAKING` with a nonzero exit status
- CloudFormation/SAM static linting with `cfn-lint 1.56.0`: pass
- All JSON documents and the architecture SVG parse successfully
- Access-key and private-key pattern scan: pass

## Cloud verification status

Cloud verification was completed in `us-east-1` on September 5, 2026, using AWS
CLI 2.36.40, AWS SAM CLI 1.166.1, and Python 3.12.10.

Observed outcomes:

- SAM validation, build, and CloudFormation deployment: pass
- Valid version 1 event: `ACCEPTED`
- Repeated event with the same idempotency key: `DUPLICATE`
- Unsupported version 2 event: `REJECTED`
- Executor record: `executionCount = 1`
- Quarantine queue: one rejected message
- EventBridge delivery dead-letter queue: zero messages
- First valid-event invocation: 3,563.92 ms duration, 3,676 ms billed, and
  111.33 ms initialization
- Duplicate-event invocation: 359.82 ms duration and 360 ms billed
- Rejected-event invocation: 330.58 ms duration and 331 ms billed

The duration values are end-to-end observations from one demonstration. They are
not a performance benchmark or a measurement of schema validation alone.

The Windows demo script was updated after cloud testing to pass the DynamoDB key
through a JSON file and to allow SQS queue metadata time to become consistent.
CloudWatch metric inspection and stack cleanup remain pending.
