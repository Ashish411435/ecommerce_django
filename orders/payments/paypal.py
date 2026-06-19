import requests
from django.conf import settings


def get_access_token():

    response = requests.post(
        f"{settings.PAYPAL_BASE_URL}/v1/oauth2/token",
        auth=(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_SECRET),
        data={"grant_type": "client_credentials"},
    )

    response.raise_for_status()
    print("Access Token: ==============", response.json()["access_token"])
    return response.json()["access_token"]
