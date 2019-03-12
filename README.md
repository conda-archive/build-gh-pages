# Build gh-pages

The purpose of this project to build docs for a PR to a Github repo and push the results to the project's gh-pages branch.

## Requirements

* aws cli setup
* npm
* virtualenv
* A token for a github user with permissions to push to your repo
* access to:
  * AWS Lambda
  * AWS KMS
  * AWS secret store

## Setup
#### Prepare AWS side
* Create a new KMS used for decrypting secrets from AWS secure store
* Go to AWS secure store and add 2 variables encrypted with the key you just created:
  * github_webhook_token: this will be the token sent with the github webhook for authentication
  * conda_bot_token: this is the user token for the GitHub account that will be used to do the required git operations

#### Prepare you machine
* Install the required npm packages
```
$ npm install package.json
```
* Install the required python packages
```
$ virtualenv venv --python=python3
$ source venv/bin/activate
$ pip install -r requirements.txt
```
* Deploy the project
```
$ serverless deploy
  ...
  Serverless: Checking Stack update progress...
  ....................
  Serverless: Stack update finished...
  Service Information
  service: build-gh-pages
  stage: dev
  region: us-east-1
  stack: build-gh-pages-dev
  resources: 14
  api keys:
    None
  endpoints:
    POST - https://devtossen4.execute-api.us-east-1.amazonaws.com/dev/build_docs
  functions:
    build_docs: build-gh-pages-dev-build_docs
    build: build-gh-pages-dev-build
  layers:
    None
  Serverless: Removing old service artifacts from S3...
```
Notice the endpoint section in the output from serverless. You will need to add this as a github webook.

#### Prepare GitHub
* Go to the setting for your github repo and add a new webhook. The URL should be the output endpoint URL from serverless, the secret should be the secret you added to AWS secure store as github_webhook_token.
