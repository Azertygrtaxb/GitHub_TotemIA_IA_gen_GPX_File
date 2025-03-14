import os
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# API Keys and Configuration
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
ORS_API_KEY = os.environ.get('ORS_API_KEY')
GMAIL_CREDENTIALS = os.environ.get('GMAIL_CREDENTIALS')

# Log API key status (without revealing the keys)
if ORS_API_KEY:
    logging.info("ORS API key is set")
    # Log full ORS API key status for debugging
    logging.info(f"ORS API key format: {ORS_API_KEY[:5]}...{ORS_API_KEY[-3:] if len(ORS_API_KEY) > 8 else ''}")
    # Confirmer que la clé a le bon format
    if not ORS_API_KEY.startswith('5b3ce3597851'):  # Format commun pour les clés ORS
        logging.warning("ORS API key format may be incorrect! Check your environment variable.")
    # Vérifier la longueur typique
    if len(ORS_API_KEY) < 20:
        logging.warning(f"ORS API key length suspicious: {len(ORS_API_KEY)} chars (should be ~40)")
else:
    logging.error("⚠️ CRITICAL: ORS API key is not set! Set the ORS_API_KEY environment variable.")
    logging.error("The application will not function correctly without a valid API key")

if OPENAI_API_KEY:
    logging.info("OpenAI API key is set")
else:
    logging.warning("OpenAI API key is not set! Set the OPENAI_API_KEY environment variable.")

# OpenRouteService API Configuration
ORS_BASE_URL = "https://api.openrouteservice.org/v2"

# Vérifier si l'environnement a changé
if 'REPLIT_DB_URL' in os.environ:
    logging.info("Running in Replit environment")
else:
    logging.info("Running in non-Replit environment")  

# Email Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = os.environ.get('SENDER_EMAIL')

# Activity Types Mapping
ACTIVITY_PROFILES = {
    'hiking': 'foot-hiking',
    'running': 'foot-walking',
    'trail': 'foot-hiking'
}

# Difficulty Levels Configuration
DIFFICULTY_SETTINGS = {
    'beginner': {
        'max_elevation_gain': 300,
        'max_distance': 10
    },
    'intermediate': {
        'max_elevation_gain': 800,
        'max_distance': 20
    },
    'expert': {
        'max_elevation_gain': 1500,
        'max_distance': 30
    }
}