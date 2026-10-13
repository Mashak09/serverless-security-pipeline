# Serverless CI/CD Security Pipeline

This is a small AWS Lambda function with a GitHub Actions pipeline around it. Every time I push code, the pipeline runs the tests, scans for security issues and only deploys to AWS if everything passes.

I built this to learn DevSecOps on a serverless setup. My previous projects used Jenkins, Kubernetes and ArgoCD. This one has no containers or clusters, so what really needs protection here is IAM.

## What is in it

- A Python 3.13 Lambda function that returns a JSON greeting on GET /hello
- API Gateway in front of it, deployed with AWS SAM
- A GitHub Actions pipeline in .github/workflows/pipeline.yml

## How the pipeline works

    push or pull request
             |
       build-and-test
             |
     +-------+---------+-----------+
     |       |         |           |
    sast  dependency secrets   template
     |       |         |           |
     +-------+---------+-----------+
             |
        deploy (main only)

The four scans run in parallel after the tests, so a full run takes about 95 seconds.

- build-and-test: installs the dependencies and runs pytest
- sast-scan: Semgrep reads my code for insecure patterns. I use the --error flag, because without it Semgrep prints the findings and still passes
- dependency-scan: pip-audit checks my libraries against known vulnerabilities
- secrets-scan: Gitleaks looks for credentials in the files and in the whole git history. It needs fetch-depth: 0, because a normal checkout only has the latest commit
- template-scan: cfn-lint checks the SAM template, then a grep check fails the job if there is a wildcard (*) in Action or Resource
- deploy: builds and deploys with SAM. It lists all four scans under needs, so one failed scan means it never starts

The pipeline runs on pushes to main and on pull requests. Deploy only runs on main, so code from a pull request is tested and scanned but never deployed.

## Project Layout

src/app.py                       the Lambda handler
tests/test_app.py                unit tests
requirements.txt                 dev dependencies (pytest)
template.yaml                    SAM template
samconfig.toml                   deploy settings
.github/workflows/pipeline.yml   the pipeline

## Security choices I made

The pipeline deploys with its own IAM user, not my personal one. If its keys ever leak, the damage is limited to this one stack.
That user’s policy is limited by resource, not only by action. It covers this stack, one S3 path, and roles and functions with this project’s name prefix.
It can only attach the basic Lambda logging policy to a role it creates. Without that condition, it could attach AdministratorAccess to a new role and give itself admin rights.
It cannot write inline role policies. If the Lambda ever needs more permissions, I have to change the policy on purpose.
The S3 bucket is set by name in samconfig.toml, so the pipeline does not need permission to create infrastructure.
The AWS keys are stored as GitHub Secrets and only the Deploy step can read them.
The runner (ubuntu-24.04) and the actions (for example checkout@v6) are pinned, so the pipeline does not change without a commit.
The Lambda itself has no custom permissions, only basic logging.

## How to set it up

You need an AWS account, a GitHub repo, Python 3.13, the AWS CLI and the SAM CLI.
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
sam build
sam deploy --guided

## Then:

Create an IAM user just for the pipeline and attach a policy limited to this stack (see the security choices above).
Create an access key for that user.
Add AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY as repository secrets in GitHub (Settings, Secrets and variables, Actions).
Push to main.

## How I tested it:

I broke each check on purpose, on a separate branch with a pull request, and looked at which job went red.
A failing test (assert 1 == 2): build-and-test failed and everything after it was skipped
An old vulnerable package (requests==2.19.0): dependency-scan failed and deploy was skipped
A fake AWS-style key in a file: secrets-scan failed
A wildcard Action in the template: template-scan failed
A normal change to the greeting: everything passed and the live URL returned the new message

## Things that went wrong

My commits did not show on my GitHub contribution graph. The author email on the EC2 machine was a made-up address. I set my git name and email, and rewrote the old commits.
The deploy failed with a strange header error. The AWS key stored in the GitHub secret had a hidden line break at the end. The clue was a \n right after the key in the error message.
GitHub rejected the workflow file twice with an “already defined” error, because I pasted a block twice. A YAML error stops the whole workflow, not just one job.
A push was rejected because I had edited the same file in the browser and on the server. I used git fetch to look at both sides, then rebased.

## What I would improve

Use OIDC, so GitHub gets temporary AWS credentials and no keys are stored at all
Replace the grep check with a proper tool like Checkov or cfn-guard, since grep misses things like s3:*
Add authentication to the API, which is public right now
Add a smoke test after the deploy
Turn on branch protection so nothing reaches main without a pull request

