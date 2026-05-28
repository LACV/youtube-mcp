#!/usr/bin/env python3
"""Full OAuth flow - opens browser, captures callback automatically."""
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import sys

CLIENT_SECRET = "/home/sistemas/Dev/mcp-servers/youtube-mcp/client_secret_pipo_reflexiona.json"
TOKEN_PATH = "/home/sistemas/Dev/mcp-servers/youtube-mcp/token_2.json"
REDIRECT_URI = "http://localhost:8081/oauth2callback"

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
]


class OAuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/oauth2callback"):
            from google_auth_oauthlib.flow import InstalledAppFlow
            
            query_string = self.path.split("?", 1)[1] if "?" in self.path else ""
            callback_url = f"{REDIRECT_URI}?{query_string}"
            
            # Send success page
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            html = """<html><body>
                <h1>✅ Autorización completada</h1>
                <p>Cerrá esta ventana.</p>
            </body></html>"""
            self.wfile.write(html.encode())
            
            # Exchange code for token
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRET, SCOPES, redirect_uri=REDIRECT_URI
            )
            try:
                flow.fetch_token(authorization_response=callback_url)
                creds = flow.credentials
                
                cred_data = {
                    'token': creds.token,
                    'refresh_token': creds.refresh_token,
                    'token_uri': creds.token_uri,
                    'client_id': creds.client_id,
                    'client_secret': creds.client_secret,
                    'scopes': list(creds.scopes),
                }
                
                with open(TOKEN_PATH, "w") as f:
                    json.dump(cred_data, f)
                
                print(f"\n✅ Token guardado en: {TOKEN_PATH}")
            except Exception as e:
                print(f"\n❌ Error: {e}", file=sys.stderr)
                sys.exit(1)
            
            import time
            threading.Thread(target=lambda: (time.sleep(2), server.shutdown()), daemon=True).start()


def main():
    from google_auth_oauthlib.flow import InstalledAppFlow

    print("🔐 YouTube OAuth - Alma Narradora")
    print("=" * 50)
    print()
    
    # Start HTTP server to receive callback
    server = HTTPServer(("127.0.0.1", 8081), OAuthHandler)
    
    # Create flow and get auth URL
    flow = InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRET, SCOPES, redirect_uri=REDIRECT_URI
    )
    auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline")

    print("1. Abrí este enlace en tu navegador:")
    print()
    print(auth_url)
    print()
    print("2. Autorizá el acceso con tu cuenta de Google")
    print("3. Se abrirá una página blanca diciendo '✅' - cerrala")
    print()
    print("4. Esperando respuesta...")
    
    import webbrowser
    try:
        webbrowser.open(auth_url)
    except Exception:
        pass
    
    server.serve_forever()


if __name__ == "__main__":
    main()
