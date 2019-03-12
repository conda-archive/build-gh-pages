import json, hashlib, hmac, git
import os, shutil
import base64, requests
from sphinx.application import Sphinx
from boto3 import client as boto3_client


lambda_client = boto3_client('lambda', region_name="us-east-1",)
ssm_client = boto3_client('ssm')


def get_secret(key):
    resp = ssm_client.get_parameter(Name=key, WithDecryption=True)
    return resp['Parameter']['Value']


def validate_signature(headers, event_body, github_webhook_token):
    try:
        signature = headers['X-Hub-Signature']
        _, sha1 = signature.split('=')
    except:
        return "Bad Request"
    digest = hmac.new(github_webhook_token.encode(), event_body.encode(), hashlib.sha1).hexdigest()
    if not hmac.compare_digest(digest.encode(), sha1.encode()):
        return "Not Authorized"


def docs_files_changed(pr_number):
    file_endpoint = "https://api.github.com/repos/conda/conda/pulls/%s/files" % (pr_number)
    files = json.loads(requests.get(file_endpoint).content)
    for file in files:
        if "docs" in file["filename"]:
            return True
    return False


def build(event, context):
    SPHINXBUILD = os.getenv('SPHINXBUILD', 'sphinx-build')
    json_payload = json.loads(event["body"])
    github_repo = json_payload["repository"]['html_url']
    trimed_github_repo = github_repo.split("//")[1]
    pr_number = json_payload["number"]
    repo_path = "/tmp/conda"
    try:
        shutil.rmtree(repo_path)
    except FileNotFoundError:
        pass

    conda_bot_token = get_secret("conda_bot_token")
    github_user = os.getenv("github_user")
    github_email = os.getenv("github_email")
    authed_repo = "https://%s:%s@%s" % (github_user, conda_bot_token, trimed_github_repo)

    git.exec_command("clone", authed_repo, repo_path)
    os.chdir(repo_path)
    git.exec_command("fetch", "origin", "+refs/pull/%s/head:pr/%s" % (pr_number, pr_number), cwd=repo_path)
    git.exec_command("checkout", "pr/%s" % pr_number, cwd=repo_path)

    docs_path = os.path.join(repo_path, "docs/source")
    confdir = docs_path
    build_output = os.path.join(repo_path, "pr-%s" % (pr_number))
    doctreedir = os.path.join(build_output, "doctrees")
    builder = "html"

    app = Sphinx(docs_path, confdir, build_output, doctreedir, builder)
    app.build()

    git.exec_command("checkout", "gh-pages", cwd=repo_path)
    git.exec_command("add", "pr-%s" % pr_number, cwd=repo_path)
    commit_env = os.environ
    commit_env['GIT_AUTHOR_NAME'] = github_user
    commit_env['GIT_AUTHOR_EMAIL'] = github_email
    commit_env['GIT_COMMITTER_NAME'] = github_user
    commit_env['GIT_COMMITTER_EMAIL'] = github_email
    git.exec_command("commit", "-m docs for pr %s" % pr_number, cwd=repo_path, env=commit_env)
    git.exec_command("push", "origin", "gh-pages", cwd=repo_path)

    response_body = "built docs change"

    response = {
        "statusCode": 200,
        "body": json.dumps(response_body)
    }
    print(response)
    return response


def build_docs(event, context):
    github_webhook_token = get_secret("github_webhook_token")
    headers = event["headers"]

    # Make sure request came from github
    try:
        event_type = headers['X-GitHub-Event']
    except KeyError:
        raise Exception("Bad Request")

    # Make sure request has valid token
    signature_response = validate_signature(headers, event["body"], github_webhook_token)
    if signature_response is not None:
        response = {
            "statusCode": 500,
            "body": "ohhhh no %s" % signature_response
        }
        return response

    if event['isBase64Encoded'] == True:
        print("Decoding body")
        event["body"] = base64.b64decode(event['body'])

    json_payload = json.loads(event["body"])
    github_repo = json_payload["repository"]['html_url']
    pr_number = json_payload["number"]
    action = json_payload["action"]

    if not docs_files_changed(pr_number):
        response_body = "no docs changes"
    else:
        print("passing off build")
        # build(event, context)
        lambda_client.invoke(
            FunctionName="build-gh-pages-dev-build",
            InvocationType='Event',
            Payload=json.dumps(event)
        )
        response_body = "building docs change"

    response = {
        "statusCode": 202,
        "body": json.dumps(response_body)
    }
    print(response)
    return response


if __name__ == "__main__":
    build_docs('', '')
