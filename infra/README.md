# AWS deployment (prepared; not yet deployed)

The meaningful AWS workload is the entire OpenCV inspection and geometric recovery pipeline in Lambda. Evidence persists in private, encrypted S3 objects; CloudWatch retains execution logs for seven days. This is an x86 deployment and does **not** claim COOL use.

## Prerequisites

An authorized AWS account and spending budget, AWS CLI credentials, Docker, and AWS SAM CLI. No credentials are stored in this repository. Do not deploy until an account owner approves the account, region, and budget. Lambda's reserved concurrency limits simultaneous execution, **not total spending**. Use AWS Budgets notifications and remove the deployment after judging.

## Build and deploy

From the repository root, run:

```text
sam validate --lint --template-file infra/template.yaml
sam build --template-file infra/template.yaml
sam deploy --guided --resolve-image-repos
```

Select the authorized region and stack name `secondcut`. Enter a randomly generated judge password of at least 20 characters into the guided parameter prompt; never put it into a tracked file. SAM creates the image repository and a narrowly scoped execution role. The function URL is public at the AWS layer; the application requires HTTP Basic authentication over HTTPS (`judge` plus the supplied password). Supply judge credentials privately in the Devpost testing instructions, not the public project story. This is a single shared judge deployment, not a multi-tenant service.

SAM provisions the resource policies for a NONE-auth function URL. Current AWS function URLs require both InvokeFunctionUrl and InvokeFunction permissions. See https://docs.aws.amazon.com/lambda/latest/dg/urls-auth.html .

## Verify before claiming deployment

Run `python scripts/check_endpoint.py https://YOUR-VERIFIED-FUNCTION-URL` and
enter the judge password at the hidden prompt. It checks authentication,
OpenCV version, five synthetic decisions, approval-gated export, and stored
verification. Credentials are not saved. Results go to the ignored
`artifacts/runtime/endpoint-check.json`. This creates five synthetic inspection
records; it does not establish cold-start persistence or physical accuracy.
Use `python scripts/check_endpoint.py http://127.0.0.1:8000 --local` for local
smoke testing without AWS access.

1. Open the stack's Endpoint output and authenticate.
2. Check `/api/health` reports OpenCV 5 and `aws-lambda`.
3. Run all five visible samples, accept a repair, download its template, and verify the generated repaired sample.
4. Repeat report retrieval after a cold start to establish S3 persistence.
5. Run a real photo through the endpoint and record latency separately from local synthetic results.
6. Save the date, region, stack output, dependency versions, and evidence in the technical report.

Lambda synchronous payload limits apply; keep uploaded photos below 4 MB for the hosted demo. Local uploads support up to 10 MB. Do not claim a working hosted endpoint until these checks pass.

## Retention and teardown

Evidence objects expire after 30 days. The bucket is retained on stack deletion to avoid accidental evidence loss. `sam delete` removes the compute stack; explicitly review the retained bucket and ECR images afterward. No automatic destructive cleanup is provided.

## Limitations

Docker image build, SAM validation, Linux dependency compatibility, S3 persistence, hosted authentication, and cloud runtime performance remain unverified until the AWS deployment is exercised. Writes are last-write-wins; the prototype assumes a single reviewer per project.
