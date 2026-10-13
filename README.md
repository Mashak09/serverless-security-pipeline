Serverless CI/CD Security pipeline
This is a small AWS Lambda function with a github actions pipeline around it.Everytime i push the
code the github pipeline runs the tests, scans for any security issues and then deploys it on AWS only
if eveyrthing passes.

I built this to learn DevSecops on a serverless setup. My previous projects used jenkins, Kubernetes and 
ArgoCD. This one has no containers or clusters. So what really needs protection over here is the IAM.

Whats in it
1.A python 3.13 lambda function that returns a JSON greeting on GET/HELLO
2. API gateway in front of it, deployed with AWS SAM
3. A Github actions pipeline in .github/workflows/pipeline.yaml

How the pipeline works:
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
The four scans run parallelly after the tests, so a full run takes about 95 seconds.
* build-and-test: installs the dependencies and runs pytest
* sast-scan: Semgrep reads my code fdor insecure patterns. I use the --error flag becasue without it
  semgrep prints the findings and still passes
* dependency-scan: pip-audit checks my libraries against known vulnerabilities.
* secret-scan: Gitleaks looks for credentials in the files and in the whole of git history.
  But it needs fetch-depth:0, because the normal checkout only has the latest commit.
* template-scan: cfn-lint checks the SAM template, then a grep check fails the job if there is a wildcard(*)
  in Action or Resouce.
* Deploy: builds and deploy with SAM. It lists all four scans under needs, so one scan means it never
  starts

The pipleine works on any pusehs to main and on pull requests. Deploy only runs on main, so code from pull 
request is tested and scanned but never deployed.
