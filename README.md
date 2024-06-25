# sagemaker-auto-shutdown

This project creates a scheduled job that delete your SageMaker endpoints and shutdown notebook instances to save cost. It is ideal for your development accounts. It will ignore resources with certain tags (default: `env:prod`, configurable). Serverless endpoints are excluded because their cost are minimal when idle.

## Configuration

* Schedule: set the `Resources > DeleteSageMakerResourcesFunction > Events > CloudWatchEvent > Properties > Schedule` in `template.yaml`. Default: every day at 20:00 UTC.
* `Parameter` in `template.yaml`:
  * EndpointExcludeTagKey: Endpoint with this tag will not be deleted.
  * EndpointExcludeTagValue: Endpoint with this tag will not be deleted.
  * NotebookExcludeTagKey: Notebook with this tag will not be stopped.
  * NotebookExcludeTagValue: Notebook with this tag will not be stopped.
* `Globals > Function > Environment > Variables` in `template.yaml`:
  * `MAX_COUNT`: The maximum number of Endpoints and Notebooks (counted separately) that is cleaned in on run. This is to limit the blast radius in case of misconfiguration.
  * `LOG_LEVEL`: log level. (`CRITICAL`, `ERROR`, `WARNING`, `INFO`, `DEBUG`. Default: `INFO`)

## Security Policy that defines permissions required for deployment
### Make sure to replace REGION and ACCOUNT with your own settings

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:Get*",
                "s3:List*",
                "s3:Describe*",
                "s3:Create*",
                "s3:Put*",
                "s3:Delete*"
            ],
            "Resource": "arn:aws:s3:::aws-sam-cli-managed-default-samclisourcebucket-*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "cloudformation:CreateChangeSet",
                "cloudformation:ExecuteChangeSet",
                "cloudformation:Describe*",
                "cloudformation:EstimateTemplateCost",
                "cloudformation:Get*",
                "cloudformation:List*",
                "cloudformation:ValidateTemplate",
                "cloudformation:Detect*",
                "cloudformation:DeleteStack"
            ],
            "Resource": [
                "arn:aws:cloudformation:<REGION>:<ACCOUNT>:stack/aws-sam-cli-managed-default/*",
                "arn:aws:cloudformation:<REGION>:aws:transform/Serverless-2016-10-31",
                "arn:aws:cloudformation:<REGION>:<ACCOUNT>:stack/sagemaker-auto-shutdown*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "iam:CreateRole",
                "iam:TagRole",
                "iam:PutRolePolicy",
                "iam:AttachRolePolicy",
                "iam:GetRole",
                "iam:PassRole",
                "iam:DeleteRolePolicy",
                "iam:DetachRolePolicy",
                "iam:DeleteRole"
            ],
            "Resource": "arn:aws:iam::<ACCOUNT>:role/sagemaker-auto-shutdown-*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "lambda:CreateFunction",
                "lambda:DeleteFunction",
                "lambda:TagResource",
                "lambda:GetFunction",
                "lambda:AddPermission",
                "lambda:RemovePermission"
            ],
            "Resource": "arn:aws:lambda:<REGION>:<ACCOUNT>:function:sagemaker-auto-shutdown-*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "events:DescribeRule",
                "events:PutRule",
                "events:PutTargets",
                "events:RemoveTargets"
            ],
            "Resource": "arn:aws:events:<REGION>:<ACCOUNT>:rule/sagemaker-auto-shutdown-*"
        }
    ]
}
```
## Deploy the application

To use the, you need the following tools:

* SAM CLI - [Install the SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
* Optional - for local testing
  * [Python 3 installed](https://www.python.org/downloads/)
  * Docker - [Install Docker community edition](https://hub.docker.com/search/?type=edition&offering=community)

To build and deploy your application for the first time, run the following in your shell:

```bash
sam deploy --guided
```

The command will package and deploy your application to AWS, with a series of prompts:

* **Stack Name**: The name of the stack to deploy to CloudFormation. This should be unique to your account and region, and a good starting point would be something matching your project name.
* **AWS Region**: The AWS region you want to deploy your app to.
* **Confirm changes before deploy**: If set to yes, any change sets will be shown to you before execution for manual review. If set to no, the AWS SAM CLI will automatically deploy application changes.
* **Allow SAM CLI IAM role creation**: Many AWS SAM templates, including this example, create AWS IAM roles required for the AWS Lambda function(s) included to access AWS services. By default, these are scoped down to minimum required permissions. To deploy an AWS CloudFormation stack which creates or modifies IAM roles, the `CAPABILITY_IAM` value for `capabilities` must be provided. If permission isn't provided through this prompt, to deploy this example you must explicitly pass `--capabilities CAPABILITY_IAM` to the `sam deploy` command.
* **Save arguments to samconfig.toml**: If set to yes, your choices will be saved to a configuration file inside the project, so that in the future you can just re-run `sam deploy` without parameters to deploy changes to your application.

## Tests
Tests are defined in the tests folder in this project. Use PIP to install the test dependencies and run tests.

```
$ pip install -r tests/requirements.txt --user
# unit test
$ python -m pytest tests/unit -v
```

## Cleanup

To delete the sample application that you created, use the AWS CLI. Assuming you used your project name for the stack name, you can run the following:

```bash
aws cloudformation delete-stack --stack-name sagemaker-auto-shutdown
```

# Contributing
See [CONTRIBUTING](CONTRIBUTING.md) for more information.

# License
See [LICENSE](LICENSE).
