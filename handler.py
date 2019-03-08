import json
import hashlib
import hmac
import git

def validate_signature(headers, event_body, github_token):
    try:
        signature = headers['X-Hub-Signature']
        _, sha1 = signature.split('=')
    except (KeyError, ValueError):
        raise Exception("Bad Request")
    digest = hmac.new(github_token.encode(), event_body.encode(), hashlib.sha1) \
        .hexdigest()
    if not hmac.compare_digest(digest.encode(), sha1.encode()):
        raise Exception("Not Authorized")

def build_docs(event, context):
    github_token = os.environ["github_token"]
    headers = event.headers;
    validate_signature(headers, event.body, github_token)

    try:
        event = request.headers['X-GitHub-Event']
    except KeyError:
        raise Exception("Bad Request")

    response = {
        "statusCode": 200,
        "body": json.dumps(event.body)
    }

    print(response)
    return response

if __name__ == "__main__":
    build_docs('', '')
