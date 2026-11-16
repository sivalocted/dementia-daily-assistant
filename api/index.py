import os
import sys

# Ensure root directory is on the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app import app as flask_app


class VercelWSGIWrapper:
    """
    Middleware ensuring that Vercel internal URL rewrites to /api/index.py
    are cleanly mapped back to the intended path in Flask WSGI environ.
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        # 1. Use HTTP_X_MATCHED_PATH header if set by Vercel
        matched_path = environ.get("HTTP_X_MATCHED_PATH")
        if matched_path:
            environ["PATH_INFO"] = matched_path

        # 2. Normalize PATH_INFO if it still points directly to the serverless function file
        path_info = environ.get("PATH_INFO", "")
        if path_info in ("/api/index.py", "/api/index", "/api", ""):
            environ["PATH_INFO"] = "/"
        elif path_info.startswith("/api/index.py/"):
            environ["PATH_INFO"] = path_info[len("/api/index.py"):]
        elif path_info.startswith("/api/index/"):
            environ["PATH_INFO"] = path_info[len("/api/index"):]

        return self.wsgi_app(environ, start_response)


# Vercel Serverless Function entry point
app = VercelWSGIWrapper(flask_app)
