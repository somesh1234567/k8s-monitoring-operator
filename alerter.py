import requests
import json
import os
from datetime import datetime
from infisical_sdk import InfisicalSDKClient
from dotenv import load_dotenv
load_dotenv()

# SLACK_URL = os.getenv("SLACK_WEBHOOK_URL")

# Initialize the client
client = InfisicalSDKClient(host="https://app.infisical.com")

client.auth.token_auth.login(token="st.ed9ce2ba-a5b5-43ff-a7cc-27afdd7f5255.f999437722ad71ae78fcf60e76ded398.0508bcf068d2f835eed124008b52803c")

secret_response = client.secrets.get_secret_by_name(secret_name="SLACK_WEBHOOK_URL", project_id="c7df3875-7e43-4d59-abea-caf68dd3a87c", environment_slug="dev", secret_path="/")
SLACK_URL = secret_response.secretValue

def send_slack_alert(message):
    if not SLACK_URL:
        print("SLACK_WEBHOOK_URL is not set. Cannot send alert.")
        return

    payload = {
        "text": message
    }
    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(SLACK_URL, data=json.dumps(payload), headers=headers)
        if response.status_code != 200:
            print(f"Failed to send alert. Status code: {response.status_code}, Response: {response.text}")
        else:
            print(f"Alert sent successfully: {message}")
    except Exception as e:
        print(f"Exception occurred while sending alert: {e}")
