import os
import requests

token = os.getenv('PAYSTACK_API_TOKEN')

def checkout(payload):
    response = requests.post(
        "https://api.paystack.co/transaction/initialize",
        json = payload,
        headers={
            "Authorization": f"Bearer {token}",
            'Content-Type': 'application/json'
        }
    )

    response_data = response.json()

    if response_data.get("status") == True:
        return True, response_data["data"]["authorization_url"]

    return False, response_data["message"]

def confirmation(reference):
    response = requests.get(
        f"https://api.paystack.co/transaction/verify/{reference}",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    return response.json()