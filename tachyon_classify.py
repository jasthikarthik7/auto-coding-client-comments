# ===============================
# tachyon.py  (modularized)
# ===============================
# Imports (from your original L1–12)
import requests
import json
import time
import uuid
import os
from datetime import datetime
from typing import List
from dotenv import load_dotenv

# keep env load (L11–12)
load_dotenv()

# -------------------------------
# Token / headers
# -------------------------------
# globals (L15–16)
cached_token = None
token_expiration_time = 0

# from L18–35
def create_headers() -> dict:
    """Creates and returns the headers for the API request."""
    try:
        request_date = datetime.now().isoformat(timespec='milliseconds') + 'Z'
        headers = {
            'x-wf-request-id': str(uuid.uuid4()),
            'x-wf-request-date': request_date,
            'x-wf-correlation-id': str(uuid.uuid4()),
            'x-wf-client-id': os.getenv('TACHYON_API_KEY'),
            'x-wf-usecase-id': 'GENAI479_1BAAS',
            'Authorization': f'Bearer {get_token()}',
            'Content-Type': 'application/json'
        }
        print("Headers created successfully")
        return headers
    except Exception as e:
        print(f"Error creating headers: {str(e)}", exc_info=True)
        raise

# from L37–86
def get_token() -> str:
    global cached_token, token_expiration_time

    # Use cached token if valid
    if cached_token and time.time() < token_expiration_time:
        print("Using cached token")
        return cached_token

    print("Requesting new authentication token")
    url = "https://apiIDP-nonprod.wellsfargo.net/oauth/token"
    payload = { 'grant_type': 'client_credentials' }
    headers = {
        'Authorization': os.getenv('API_CONSUMER_AUTH'),
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    try:
        print(f"Making token request to {url}")
        response = requests.request("POST", url, headers=headers, data=payload, verify="certs/root.crt")
        response.raise_for_status()

        # Parse JSON (L58–75)
        try:
            response_json = response.json()
        except json.JSONDecodeError:
            error_msg = "Failed to fetch token: Invalid JSON"
            print(error_msg)
            raise ValueError(error_msg)

        cached_token = response_json.get("access_token")
        expires_in   = response_json.get("expires_in", 0)

        if not cached_token:
            error_msg = "Failed to fetch token: Missing access_token in response"
            print(error_msg)
            raise ValueError(error_msg)

        token_expiration_time = time.time() + expires_in
        print(f"New token obtained, expires in {expires_in} seconds")

        return cached_token

    except requests.exceptions.RequestException as e:
        print(f"Network error while fetching token: {str(e)}", exc_info=True)
        raise
    except Exception as e:
        print(f"Unexpected error in get_token: {str(e)}", exc_info=True)
        raise

# -------------------------------
# Generation call
# -------------------------------
# from L102–136 (unchanged behavior, only wrapped)
def generate(messages: List, response_schema=None):
    print("Generating response from model")
    url = "https://apigw-uat.wellsfargo.net/analytics-data-management/artificialintelligence-machinelearn"

    payload = {
        "model": "gemini_pro_gcp",
        "modeli": "gemini-2.5-flash",
        "messages": messages,
        "top_p": 1,
        "temperature": 0,
    }
    if response_schema:
        payload["response_format"] = response_schema

    payload = json.dumps(payload)

    try:
        headers = create_headers()
        print(f"Making generation request to {url} with payload {payload}")
        start_time = time.time()
        response = requests.request("POST", url, headers=headers, data=payload, verify="certs/root.crt")
        elapsed_time = time.time() - start_time
        print(f"Generation request completed in {elapsed_time:.2f} seconds")
        response.raise_for_status()

        try:
            response_json = response.json()
            print("Generation response received and parsed")
        except json.JSONDecodeError:
            # retain original behavior: return raw text if not JSON
            logger.warning("Generation response is not valid JSON")
            return response.text

        if 'choices' not in response_json or len(response_json['choices']) == 0:
            error_msg = "Generation response missing expected content"
            print(error_msg)
            return f"Error: {error_msg}"

        response_content = response_json['choices'][0]['message']['content']
        print(f"Generated response of length {len(response_content)}")
        return response_content

    except Exception as e:
        print(f"Error during generation: {str(e)}", exc_info=True)
        raise
