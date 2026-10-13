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
