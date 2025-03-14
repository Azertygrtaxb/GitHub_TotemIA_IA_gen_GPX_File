import openai
from config import OPENAI_API_KEY
import logging
import json

# the newest OpenAI model is "gpt-4o" which was released May 13, 2024
openai.api_key = OPENAI_API_KEY


def generate_route_description(preferences):
    """Generate an engaging route description based on user preferences."""

    # Map duration values to human-readable format
    duration_map = {
        '0.5': '30 minutes',
        '1': '1 heure',
        '2': '2 heures ou plus'
    }

    prompt = f"""
    Create an engaging route description that STRICTLY adheres to these exact specifications:

    Core Requirements (MUST be followed exactly):
    - Activity Type: {preferences['activity_type']} (non-negotiable)
    - Location: {preferences['location']} (exact location)
    - Distance: EXACTLY {preferences['distance']}km (no more, no less)
    - User Level: {preferences['level']}
    - Landscape: {preferences['landscape']} type terrain only

    Specific Route Parameters (to be followed precisely):
    - Route Structure: {preferences['route_type']} ('loop' for circular route, 'roundtrip' for out-and-back)
    - Elevation Profile: {preferences['elevation_preference']} ('flat', 'moderate', or 'hilly')
    - Target Duration: {duration_map[preferences['duration']]} (pace must match this duration)
    - Surface Type: {preferences['surface_type']} (must stick to this surface type)
    - Points of Interest: {preferences['points_of_interest']} (if specified)

    IMPORTANT VERIFICATION STEPS:
    1. The route MUST be EXACTLY {preferences['distance']}km
    2. The route MUST follow a {preferences['route_type']} structure
    3. The terrain MUST be {preferences['surface_type']} type only
    4. The duration MUST match {duration_map[preferences['duration']]} exactly
    5. The elevation profile MUST match {preferences['elevation_preference']} preference

    Focus on creating a route that matches ALL these criteria exactly. 
    If ANY of these requirements cannot be met exactly, respond with an error message.

    Provide the response in the following strict JSON format:
    {{
        "title": "Precise route title including exact distance and duration",
        "description": "Detailed description emphasizing how each requirement is met precisely",
        "highlights": [
            "First key point focusing on exact requirements met",
            "Second key point on matching criteria",
            "Third key point on specific parameters achieved"
        ],
        "difficulty_notes": "Notes about meeting the exact duration and distance requirements",
        "verification": {{
            "distance_match": true,
            "duration_match": true,
            "route_type_match": true,
            "surface_match": true,
            "elevation_match": true
        }}
    }}
    """

    try:
        logging.debug(f"Sending OpenAI request with preferences: {preferences}")
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": prompt
            }],
            response_format={"type": "json_object"})

        response_content = response.choices[0].message.content
        logging.debug(f"Received OpenAI response: {response_content}")

        # Validate JSON structure
        try:
            json_response = json.loads(response_content)
            # Verify required fields
            required_fields = ['title', 'description', 'highlights', 'difficulty_notes', 'verification']
            for field in required_fields:
                if field not in json_response:
                    raise ValueError(f"Missing required field: {field}")
            return response_content
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON response: {str(e)}")
            raise Exception("Failed to parse route description: Invalid JSON format")
        except ValueError as e:
            logging.error(f"Invalid response structure: {str(e)}")
            raise Exception(f"Invalid route description format: {str(e)}")

    except Exception as e:
        logging.error(f"Failed to generate route description: {str(e)}")
        raise Exception(f"Failed to generate route description: {str(e)}")