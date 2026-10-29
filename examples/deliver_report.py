"""Agent -> human: save a report and return a 24h, 3-open link. Needs only `pip install requests`."""
import base64, os, requests

BASE = "https://hand-off.space"
H = {"authorization": f"Bearer {os.environ['HANDOFF_API_KEY']}"}

def share_file(path: str, mime: str = "application/pdf", hours: int = 24, opens: int = 3) -> str:
    with open(path, "rb") as f:
        body = {"name": os.path.basename(path), "mime": mime, "content_base64": base64.b64encode(f.read()).decode()}
    file_id = requests.post(f"{BASE}/v1/files", json=body, headers=H, timeout=60).json()["id"]
    grant = requests.post(f"{BASE}/v1/files/{file_id}/grants", headers=H, timeout=30,
                          json={"audience": "anyone_with_link", "expires_in_hours": hours, "max_opens": opens}).json()
    return grant["url"]

if __name__ == "__main__":
    import sys
    print(share_file(sys.argv[1]))
