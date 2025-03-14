from flask import Flask
import os
import logging

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Import routes after app initialization
from routes import *  # noqa

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
