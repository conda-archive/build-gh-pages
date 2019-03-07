import json
import git

def build_docs(event, context):
    body = {
        "message": "Go Serverless v1.0! Your function executed successfully!",
        "input": event
    }

    response = {
        "statusCode": 200,
        "body": json.dumps(body)
    }

    print(response)
    return response

if __name__ == "__main__":
    build_docs('', '')
