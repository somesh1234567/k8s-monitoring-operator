import os
import kopf
import kubernetes
import yaml

@kopf.on.create('ephemeralvolumeclaims')
def create_fn(spec, name, namespace, logger, **kwargs):

    size = spec.get('size')
    if not size:
        raise kopf.PermanentError(f"Size must be set. Got {size!r}.")

    path = os.path.join(os.path.dirname(__file__), 'pvc.yaml')
    tmpl = open(path, 'rt').read()
    text = tmpl.format(name=name, size=size)
    data = yaml.safe_load(text)

    kopf.adopt(data)

    api = kubernetes.client.CoreV1Api()
    obj = api.create_namespaced_persistent_volume_claim(
        namespace=namespace,
        body=data,
    )

    logger.info(f"PVC child is created: {obj}")
    return {'pvc-name': obj.metadata.name}

@kopf.on.field('ephemeralvolumeclaims', field='metadata.labels')
def relabel(diff, status, namespace, logger, **kwargs):
    # Use .get() to avoid KeyError
    create_status = status.get('create_fn')
    if not create_status:
        # If create_fn didn't run or return anything, we can't find the PVC
        logger.warning("No 'create_fn' status found. Has the PVC been created yet?")
        return

    pvc_name = create_status.get('pvc-name')
    if not pvc_name:
        logger.warning("PVC name not found in status. Skipping label sync.")
        return

    # Process the diff as before
    labels_patch = {}
    for op, field, old, new in diff:
        if not field:
            labels_patch.update(new if new else {})
        else:
            labels_patch[field[0]] = new

    pvc_patch = {'metadata': {'labels': labels_patch}}

    api = kubernetes.client.CoreV1Api()
    api.patch_namespaced_persistent_volume_claim(
        namespace=namespace,
        name=pvc_name,
        body=pvc_patch,
    )
    logger.info(f"Updated labels on PVC {pvc_name}")
