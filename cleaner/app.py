import json
import boto3
import logging
import os

logger = logging.getLogger()
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())

print(logger.level)

def try_parse_env(key):
    if key not in os.environ:
        logger.warning("%s not set.", key)
    else:
        try:
            return json.loads(os.getenv(key, "null"))
        except Exception as e:
            logger.error("Invalid syntax for %s, abort to avoid deleting resources.", key)
            raise e

def parse_config():
    return {
        "ENDPOINT_EXCLUDE_TAG": try_parse_env("ENDPOINT_EXCLUDE_TAG"),
        "NOTEBOOK_EXCLUDE_TAG": try_parse_env("NOTEBOOK_EXCLUDE_TAG"),
        "MAX_COUNT": try_parse_env("MAX_COUNT") or 100,
    }

def is_serverless_endpoint(client, endpoint_name):
    endpoint = client.describe_endpoint(EndpointName = endpoint_name)
    endpoint_config = client.describe_endpoint_config(EndpointConfigName = endpoint["EndpointConfigName"])
    product_variants = endpoint_config["ProductionVariants"]
    return "ServerlessConfig" in product_variants[0]

def get_endpoint_names(client, config):
    logger.info('Getting InService endpoints')
    endpoint_names = []
    endpoints =  client.list_endpoints(
        SortBy = 'CreationTime',
        SortOrder = 'Descending',
        StatusEquals = 'InService',
        MaxResults = config["MAX_COUNT"]
    )["Endpoints"]
    
    for each in endpoints:
        name = each["EndpointName"]
        tags = client.list_tags(ResourceArn = each["EndpointArn"])
        if config["ENDPOINT_EXCLUDE_TAG"] in tags['Tags']:
            logger.debug('Ignoring because of tag: %s', name)
            continue
        if is_serverless_endpoint(client, name):
            logger.debug('Ignoring because of serverless endpoint: %s', name)
            continue
        logger.debug('Will delete: %s', name)
        endpoint_names.append(name)
    return endpoint_names

def get_notebook_names(client, state, config):
    logger.info('Getting %s notebooks', state)
    notebook_names = []
    notebooks = client.list_notebook_instances(
        SortBy = 'CreationTime',
        SortOrder = 'Descending',
        StatusEquals = state,
        MaxResults = config["MAX_COUNT"]
    )["NotebookInstances"]
    for each in notebooks:
        if each['NotebookInstanceStatus'] == state:
            name = each["NotebookInstanceName"]
            tags = client.list_tags(ResourceArn = each["NotebookInstanceArn"])
            if config["NOTEBOOK_EXCLUDE_TAG"] in tags['Tags']:
                logger.debug('Ignoring because of tag: %s', name)
                continue
            logger.debug('Will delete: %s', name)
            notebook_names.append(name)
    return notebook_names

def delete_endpoints(client, endpoint_names):
    logger.info('Deleting endpoints')
    count = 0
    for name in endpoint_names:
        client.delete_endpoint(EndpointName = name)
        count += 1
    logger.info('Deleted %s endpoints', count)
    return

def stop_notebook_instances(client, notebook_names):
    logger.info('Stopping notebooks')
    count = 0
    for name in notebook_names:
        try:
            client.stop_notebook_instance(NotebookInstanceName = name)
            count += 1
        except:
            continue
    logger.info('Stopped %s notebooks', count)
    return

def get_jupyterlab_apps(client, state, config):
    logger.info('Getting %s jupyter apps', state)
    jupyterlab_apps = []
    apps = client.list_apps()["Apps"]
    for each in apps:
        if each['Status'] == state and each['AppType'] == 'JupyterLab':
            app_name = each['AppName']
            app_type = 'JupyterLab'
            domain_id = each['DomainId']
            space_name = each['SpaceName']
            logger.debug('Will delete jupyterlab app: %s', app_name)
            jupyterlab_apps.append(
                {
                    "AppName": app_name,
                    "AppType": app_type,
                    "DomainId": domain_id,
                    "SpaceName": space_name
                }
            )
    return jupyterlab_apps

def delete_jupypterlab_apps(client, apps):
    logger.info('Deleting jupyterlab apps')
    count = 0
    for app in apps:
        try:
            client.delete_app(
                DomainId=app['DomainId'],
                SpaceName=app['SpaceName'],
                AppType=app['AppType'],
                AppName=app['AppName']
            )
            count += 1
        except:
            countinue
    logger.info('Deleted %s jupyterlab apps', count)
    return

def lambda_handler(event, context):

    client = boto3.client('sagemaker')
    
    config = parse_config()

    endpoint_names = get_endpoint_names(client, config)
    delete_endpoints(client, endpoint_names)

    notebook_names = get_notebook_names(client, 'InService', config)
    stop_notebook_instances(client, notebook_names)

    jupyterlab_apps = get_jupyterlab_apps(client, 'InService', config)
    delete_jupypterlab_apps(client, jupyterlab_apps)

    return {
        'statusCode': 200,
        'body': json.dumps('Completed lambda function to clean SageMaker resources.')
    }
