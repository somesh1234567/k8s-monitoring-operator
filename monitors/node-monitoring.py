from asyncio.log import logger
import datetime
import kopf
import kubernetes
from kubernetes import client, config
from alerter import send_slack_alert

alert_cooldown = {} #type: dict[str, float]
COOLDOWN_PERIOD = 300  # Cooldown period in seconds (5 minutes)

@kopf.on.startup()
def startup_fn(logger, **kwargs):
    logger.info("Starting up the operator. Monitoring has begun......!!!")
    try:
        config.load_incluster_config()
        print("Running inside Kubernetes cluster")
    except:
        config.load_kube_config()
        print("Running outside Kubernetes cluster")

# Watch node events and log them
@kopf.on.event('', 'v1', 'nodes')
def node_event(event, body, logger, **kwargs):
    node_name = body['metadata']['name']
    conditions = body.get('status', {}).get('conditions', [])
    for condition in conditions:
        if condition['type'] == 'Ready':
            logger.info(f"Node {node_name} | Ready: {condition['status']}")

# fuction to check if the alert can be sent based on cooldown
def can_send_alert(node_name):
    current_time = datetime.datetime.now().timestamp()
    last_alert_time = alert_cooldown.get(node_name, 0.0)
    if current_time - last_alert_time > COOLDOWN_PERIOD:
        alert_cooldown[node_name] = current_time
        return True
    return False

# Helper function to convert the memory in Ki to Mb
def convert_memory(memory_str):
    if memory_str.endswith('Ki'):
        return int(memory_str[:-2]) / 1024
    return 0

# Watch the node and collects metrics and logs them
@kopf.timer('', 'v1', 'nodes', interval=30)
def monitor_node(body, logger, **kwargs):
    node_name = body['metadata']['name']
    custom_api = client.CustomObjectsApi()
    try:
        metrics = custom_api.get_cluster_custom_object(
            group="metrics.k8s.io",
            version="v1beta1",
            plural="nodes",
            name=node_name
        )
        cpu = metrics['usage']['cpu']
        memory_in_mb = convert_memory(metrics['usage']['memory'])
        memory_threshold = 500  # threshold for memory usage in MB
        if memory_in_mb > memory_threshold:
            if can_send_alert(node_name):
                logger.warning(f"Node {node_name} is using high memory: {memory_in_mb} MB")
                send_slack_alert(f"Node {node_name} is using high memory: {memory_in_mb} MB")
        else:
            logger.info(f"Node {node_name} | CPU Usage: {cpu} | Memory Usage: {memory_in_mb} MB")
    except Exception as e:
        logger.warning(f"Failed to fetch metrics for node {node_name}: {e}")
