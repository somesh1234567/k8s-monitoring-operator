import datetime

alert_cooldown = {} #type: dict[str, float]
COOLDOWN_PERIOD = 300  # Cooldown period in seconds (5 minutes)

def can_send_alert(resource_name):
    current_time = datetime.datetime.now().timestamp()
    last_alert_time = alert_cooldown.get(resource_name, 0.0)
    if current_time - last_alert_time > COOLDOWN_PERIOD:
        alert_cooldown[resource_name] = current_time
        return True
    return False