import requests
import json
import os
from datetime import datetime

SLACK_URL = os.getenv("SLACK_WEBHOOK_URL")

if not SLACK_URL:
    print("SLACK_WEBHOOK_URL not found in environment. Falling back to Infisical SDK for local testing...")
    from infisical_sdk import InfisicalSDKClient  # type: ignore
    from dotenv import load_dotenv
    load_dotenv()

    # Initialize the client
    client = InfisicalSDKClient(host="https://app.infisical.com")

    client.auth.token_auth.login(token=os.getenv("INFISICAL_TOKEN"))

    secret_response = client.secrets.get_secret_by_name(secret_name="SLACK_WEBHOOK_URL", project_id=os.getenv("INFISICAL_PROJECT_ID"), environment_slug="dev", secret_path="/")
    SLACK_URL = secret_response.secretValue
    print("SLACK_WEBHOOK_URL fetched successfully from Infisical SDK.")
else:
    print("SLACK_WEBHOOK_URL found in environment. Using production mode.")


# Main processing function to send alert to Slack
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
