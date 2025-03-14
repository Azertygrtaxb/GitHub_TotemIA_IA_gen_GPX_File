import logging
import sys
sys.path.append('.')

from services.email_service import EmailService
from services.openai_service import generate_route_description

# Configure logging
logging.basicConfig(level=logging.DEBUG)

def test_email_personalization():
    # Sample test data
    test_preferences = {
        'activity_type': 'hiking',
        'level': 'intermediate',
        'landscape': 'forest',
        'distance': '10',
        'route_type': 'loop',
        'elevation_preference': 'moderate',
        'duration': '1',
        'surface_type': 'dirt',
        'points_of_interest': 'panoramic',
        'location': 'Quimper'
    }
    
    # Sample route description
    sample_description = {
        'title': 'Randonnée forestière de 10km à Quimper',
        'description': 'Un magnifique parcours en boucle à travers les bois.',
        'highlights': [
            'Sentiers ombragés et bien balisés',
            'Points de vue panoramiques',
            'Terrain varié idéal pour niveau intermédiaire'
        ],
        'difficulty_notes': 'Parcours modéré avec quelques montées',
        'verification': {
            'distance_match': True,
            'duration_match': True,
            'route_type_match': True,
            'surface_match': True,
            'elevation_match': True
        }
    }

    # Sample GPX content
    sample_gpx = """<?xml version="1.0" encoding="UTF-8"?>
    <gpx version="1.1">
        <trk><name>Test Route</name></trk>
    </gpx>"""

    email_service = EmailService()
    
    try:
        # Test email generation
        email_service.send_gpx_email(
            recipient_email="test@example.com",
            gpx_content=sample_gpx,
            route_description=sample_description,
            preferences=test_preferences
        )
        print("Email personalization test completed successfully")
        
    except Exception as e:
        print(f"Email personalization test failed: {str(e)}")
        raise

if __name__ == "__main__":
    test_email_personalization()
