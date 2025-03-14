import os
import json
import requests
import gpxpy
import gpxpy.gpx
from typing import Dict, Optional, Tuple
import logging

logging.basicConfig(level=logging.DEBUG)


class RouteGenerator:
    def __init__(self):
        self.api_key = os.environ.get('OPENROUTE_API_KEY')
        self.base_url = "https://api.openrouteservice.org"

    def _get_profile(self, activity_type: str) -> str:
        """Convert activity type to ORS profile"""
        profiles = {
            'walking': 'foot-walking',
            'hiking': 'foot-hiking',
            'trail': 'foot-hiking',
            'running': 'foot-walking'  # Added running profile
        }
        return profiles.get(activity_type.lower(), 'foot-hiking')

    def generate_route(self, 
                      start_coords: Tuple[float, float],
                      preferences: Dict) -> Optional[Dict]:
        """
        Generate a route using OpenRouteService API
        """
        try:
            profile = self._get_profile(preferences['activity_type'])

            # Convert distance from km to meters and ensure it's a float
            distance_meters = float(preferences['distance']) * 1000

            # Prepare the request body for ORS API
            body = {
                "coordinates": [start_coords],
                "profile": profile,
                "preference": "recommended",
                "units": "km",
                "language": "fr",
                "instructions": True,
                "elevation": True,
                "options": {
                    "round_trip": {
                        "length": distance_meters,  # Use converted distance
                        "points": 5,
                        "seed": 1
                    }
                }
            }

            logging.debug(f"Sending request to ORS API with body: {json.dumps(body)}")

            # Make request to ORS API
            response = requests.post(
                f"{self.base_url}/v2/directions/{profile}/geojson",
                json=body,
                headers={
                    'Authorization': self.api_key,
                    'Content-Type': 'application/json'
                }
            )
            response.raise_for_status()

            route_data = response.json()
            logging.debug(f"Received response from ORS API: {json.dumps(route_data)}")

            # Convert GeoJSON to GPX
            gpx_content = self._convert_to_gpx(route_data, preferences)

            return {
                'gpx_content': gpx_content,
                'coordinates': json.dumps(route_data['features'][0]['geometry']['coordinates']),
                'distance': route_data['features'][0]['properties']['segments'][0]['distance'],
                'elevation_gain': route_data['features'][0]['properties']['segments'][0]['ascent']
            }

        except Exception as e:
            logging.error(f"Error generating route: {str(e)}")
            return None

    def _convert_to_gpx(self, geojson_data: Dict, preferences: Dict) -> str:
        """Convert GeoJSON route to GPX format"""
        gpx = gpxpy.gpx.GPX()

        # Create track
        track = gpxpy.gpx.GPXTrack()
        gpx.tracks.append(track)

        # Create segment
        segment = gpxpy.gpx.GPXTrackSegment()
        track.segments.append(segment)

        # Add points
        coordinates = geojson_data['features'][0]['geometry']['coordinates']
        for coord in coordinates:
            segment.points.append(gpxpy.gpx.GPXTrackPoint(
                latitude=coord[1],
                longitude=coord[0],
                elevation=coord[2] if len(coord) > 2 else None
            ))

        # Add metadata
        gpx.name = f"Parcours {preferences['activity_type']} - {preferences.get('location', 'Bretagne')}"
        gpx.description = (
            f"Parcours {preferences['distance']}km - "
            f"Niveau {preferences.get('level', 'Intermédiaire')} - "
            f"Type: {preferences.get('landscape', 'Varié')}"
        )
        gpx.author_name = "Sport Outdoor Route Generator"

        return gpx.to_xml()