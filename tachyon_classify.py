import requests

TACHYON_API_URL = "https://your-tachyon-endpoint/api"
API_KEY = "your-api-key"

def classify_with_tachyon(comment: str) -> str:
    payload = {
        "prompt": f"Classify this customer comment into one of the following categories: "
                  f"Functionality, Move Money, Navigation, Statements, Other\n\n"
                  f"Comment: \"{comment}\"\nCategory:",
        "temperature": 0,
        "max_tokens": 10
    }
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post(TACHYON_API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        result = response.json()
        return result.get("text", "").strip()
    else:
        return "Other"