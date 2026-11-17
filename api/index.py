import os
import sys
import urllib.parse

# Ensure root directory is on the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app import app as flask_app


class VercelWSGIWrapper:
    """
    WSGI Middleware ensuring Vercel internal URL rewrites are cleanly
    mapped back to the actual client-requested route via __vercel_path.
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        query_string = environ.get("QUERY_STRING", "")
        if "__vercel_path=" in query_string:
            params = urllib.parse.parse_qs(query_string, keep_blank_values=True)
            if "__vercel_path" in params:
                raw_path = params.pop("__vercel_path")[0]
                clean_path = "/" + raw_path.lstrip("/")
                environ["PATH_INFO"] = clean_path if clean_path else "/"
                # Re-encode remaining query parameters
                flat_params = [(k, v) for k, vs in params.items() for v in vs]
                environ["QUERY_STRING"] = urllib.parse.urlencode(flat_params)
        else:
            path_info = environ.get("PATH_INFO", "")
            if path_info in ("/api/index.py", "/api/index", "/api", ""):
                environ["PATH_INFO"] = "/"
            elif path_info.startswith("/api/index.py/"):
                environ["PATH_INFO"] = path_info[len("/api/index.py"):]
            elif path_info.startswith("/api/index/"):
                environ["PATH_INFO"] = path_info[len("/api/index"):]

        return self.wsgi_app(environ, start_response)


# Apply WSGI middleware directly to Flask's wsgi_app
flask_app.wsgi_app = VercelWSGIWrapper(flask_app.wsgi_app)

# Expose both app and handler for Vercel Python runtime
app = flask_app
handler = flask_app
