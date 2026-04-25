import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import kopf
from kubernetes import client, config  # type: ignore
from utils.converters import convert_cpu, convert_memory
from utils.cooldown import can_send_alert
from alerter import send_slack_alert
from config import MEMORY_THRESHOLD_MB, CPU_THRESHOLD_MILLICORES, EXCLUDED_NAMESPACES


@kopf.timer('', 'v1', 'pods', interval=30)
def monitor_pods(body, logger, **kwargs):
    pod_name = body['metadata']['name']
    namespace = body['metadata']['namespace']

    if namespace in EXCLUDED_NAMESPACES:
        return
    
    phase = body.get('status', {}).get('phase', '')
    if phase != 'Running':
        logger.warning(f"Pod {pod_name} in namespace {namespace} is in {phase} phase.")
        return
    
    custom_api = client.CustomObjectsApi()
    try:
        metrics = custom_api.get_namespaced_custom_object(
            group="metrics.k8s.io",
            version="v1beta1",
            plural="pods",
            namespace=namespace,
            name=pod_name
        )
        total_cpu = 0
        total_memory = 0
        for container in metrics['containers']:
            total_cpu += convert_cpu(container['usage']['cpu'])
            total_memory += convert_memory(container['usage']['memory'])

            if total_memory > MEMORY_THRESHOLD_MB:
                if can_send_alert(pod_name):
                    logger.warning(f"Pod {pod_name} in namespace {namespace} is using {total_memory:.2f} MB of memory, which exceeds the threshold of {MEMORY_THRESHOLD_MB} MB.")
                    send_slack_alert(
                    f"🟠 *Pod High Memory*\n"
                    f"Pod: `{pod_name}`\n"
                    f"Namespace: `{namespace}`\n"
                    f"Memory: `{total_memory:.1f} MB` (threshold: {MEMORY_THRESHOLD_MB} MB)"
                    )
            if total_cpu > CPU_THRESHOLD_MILLICORES:
                if can_send_alert(pod_name):
                    logger.warning(f"Pod {pod_name} in namespace {namespace} is using {total_cpu:.2f} millicores of CPU, which exceeds the threshold of {CPU_THRESHOLD_MILLICORES} millicores.")
                    send_slack_alert(
                    f"🟠 *Pod High CPU*\n"
                    f"Pod: `{pod_name}`\n"
                    f"Namespace: `{namespace}`\n"
                    f"CPU: `{total_cpu:.1f} millicores` (threshold: {CPU_THRESHOLD_MILLICORES} millicores)"
                    )
            else:
                logger.info(f"Pod {pod_name} in namespace {namespace} is using {total_cpu:.2f} millicores of CPU and {total_memory:.2f} MB of memory, which are within the thresholds.")
    except Exception as e:
        logger.error(f"Error fetching metrics for pod {pod_name} in namespace {namespace}: {e}")
