import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


import kopf
from kubernetes import config  # type: ignore

import monitors.pod
import monitors.node

@kopf.on.startup()
def startup_fn(logger, **kwargs):
    logger.info("Starting up the operator...")
    try:
        config.load_incluster_config()
    except:
        config.load_kube_config()