# Publishing Checklist

## Before cloud deployment

- [x] Root-user MFA is enabled.
- [x] No root or IAM access keys were created.
- [x] The $10 monthly budget alert is active.
- [x] AWS CLI login identifies `user/community-builder-dev`.
- [x] Python 3.12 and SAM CLI are installed.
- [x] Nine local tests pass.
- [x] The 1.1.0 compatibility check passes.
- [x] The intentionally breaking 2.0.0 check fails.

## Cloud verification

- [x] `sam validate --lint` passes.
- [x] CloudFormation change set contains only expected resources.
- [x] Stack deployment completes in `us-east-1`.
- [x] Valid event returns `ACCEPTED`.
- [x] Repeated event returns `DUPLICATE`.
- [x] Breaking event returns `REJECTED`.
- [x] Executor table shows `executionCount = 1`.
- [x] Quarantine queue contains the rejected event.
- [x] Delivery DLQ remains empty.
- [ ] CloudWatch metrics appear.
- [ ] Stack cleanup completes after evidence is captured.

## Repository publication

- [ ] Create the repository under your personal GitHub account.
- [x] Insert the final GitHub repository URL in `ARTICLE.md`.
- [ ] Confirm there are no employer names, data, credentials, account IDs, or ARNs.
- [ ] Enable GitHub private vulnerability reporting.
- [ ] Push source and create the `v1.0.0` release.
- [ ] Keep the Apache 2.0 license.
- [ ] Add repository topics such as `aws`, `eventbridge`, `json-schema`, and `agents`.

## Builder Center article

- [x] Replace every `TBD after cloud test` with observed results.
- [ ] Upload the architecture diagram with meaningful alt text.
- [ ] Add one redacted screenshot showing the three statuses.
- [ ] Link to the tagged GitHub release, not only the default branch.
- [ ] Describe the project as an independent community sample.
- [ ] Do not imply AWS reviewed, endorsed, or adopted it.
- [ ] Preview the article on desktop and mobile before publishing.

## Evidence preservation

- [ ] Save the publication URL and a dated PDF.
- [ ] Save the AWS Community Builder profile and contribution listing.
- [ ] Capture views, likes, comments, shares, clones, and unique visitors periodically.
- [ ] Preserve independent issues, pull requests, citations, and adopter statements.
- [ ] Keep records factual; do not manufacture engagement or adoption.
