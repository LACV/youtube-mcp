"""Authentication utilities for YouTube API."""

import json
from pathlib import Path
from typing import Optional
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
]


def load_credentials(token_path: str) -> Optional[Credentials]:
    """Load credentials from token file."""
    token_path = Path(token_path)
    if not token_path.exists():
        return None
    
    try:
        with open(token_path) as f:
            cred_data = json.load(f)
        return Credentials(
            token=cred_data.get("token"),
            refresh_token=cred_data.get("refresh_token"),
            token_uri=cred_data.get("token_uri"),
            client_id=cred_data.get("client_id"),
            client_secret=cred_data.get("client_secret"),
            scopes=cred_data.get("granted_scopes"),
        )
    except Exception:
        return None


def save_credentials(creds: Credentials, token_path: str) -> None:
    """Save credentials to token file."""
    with open(token_path, "w") as f:
        f.write(creds.to_json())


def authenticate(client_secret_path: str, token_path: str) -> Optional[Credentials]:
    """Authenticate with YouTube API."""
    if not Path(client_secret_path).exists():
        print(f"  ⚠️  Client secret not found: {client_secret_path}")
        return None
    
    # Load existing credentials
    creds = load_credentials(token_path)
    
    # Refresh if expired
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            save_credentials(creds, token_path)
        except Exception as e:
            print(f"  ⚠️  Could not refresh token: {e}")
            creds = None
    
    # Authenticate from scratch if needed
    if not creds or not creds.valid:
        print(f"  🔐 Authenticating with YouTube...")
        flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, SCOPES)
        creds = flow.run_local_server(host="127.0.0.1", port=0)
        save_credentials(creds, token_path)
        print(f"  ✅ Token saved: {token_path}")
    
    return creds
