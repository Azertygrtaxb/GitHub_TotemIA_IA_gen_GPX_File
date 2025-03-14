import requests
from typing import Optional, Tuple
from dataclasses import dataclass

@dataclass
class Location:
    name: str
    latitude: float
    longitude: float
    is_in_brittany: bool

class LocationValidator:
    BRITTANY_BOUNDING_BOX = {
        'min_lat': 47.1,
        'max_lat': 48.9,
        'min_lon': -5.2,
        'max_lon': -1.0
    }

    @staticmethod
    def validate_brittany_location(location_name: str) -> Optional[Location]:
        """
        Validates if a given location is in Brittany and returns its coordinates.
        Uses Nominatim API for geocoding.
        """
        try:
            # Use Nominatim API to get coordinates
            response = requests.get(
                f"https://nominatim.openstreetmap.org/search",
                params={
                    'q': f"{location_name}, Bretagne, France",
                    'format': 'json',
                    'limit': 1
                },
                headers={'User-Agent': 'SportOutdoorRouteGenerator/1.0'}
            )
            response.raise_for_status()
            
            if not response.json():
                return None
                
            location_data = response.json()[0]
            lat = float(location_data['lat'])
            lon = float(location_data['lon'])
            
            # Check if coordinates are within Brittany's bounding box
            is_in_brittany = (
                LocationValidator.BRITTANY_BOUNDING_BOX['min_lat'] <= lat <=
                LocationValidator.BRITTANY_BOUNDING_BOX['max_lat'] and
                LocationValidator.BRITTANY_BOUNDING_BOX['min_lon'] <= lon <=
                LocationValidator.BRITTANY_BOUNDING_BOX['max_lon']
            )
            
            return Location(
                name=location_name,
                latitude=lat,
                longitude=lon,
                is_in_brittany=is_in_brittany
            )
            
        except Exception as e:
            print(f"Error validating location: {str(e)}")
            return None
