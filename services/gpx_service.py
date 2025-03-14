import gpxpy
import gpxpy.gpx
from datetime import datetime
import logging

class GPXService:
    @staticmethod
    def create_gpx(route_data, preferences):
        """Convert route data to GPX format."""
        try:
            logging.debug(f"Creating GPX from route data: {route_data}")
            gpx = gpxpy.gpx.GPX()

            # Create first track in our GPX
            gpx_track = gpxpy.gpx.GPXTrack()
            gpx.tracks.append(gpx_track)

            # Create first segment in our track
            gpx_segment = gpxpy.gpx.GPXTrackSegment()
            gpx_track.segments.append(gpx_segment)

            # Extract coordinates from GeoJSON format
            if not route_data.get('features') or not route_data['features']:
                raise Exception("No route features found in response")

            coordinates = route_data['features'][0]['geometry']['coordinates']
            if not coordinates:
                raise Exception("No coordinates found in route data")

            logging.debug(f"Processing {len(coordinates)} coordinates")

            # Create points from coordinates [longitude, latitude, elevation]
            for coord in coordinates:
                try:
                    point = gpxpy.gpx.GPXTrackPoint(
                        latitude=coord[1],  # GeoJSON uses [longitude, latitude] order
                        longitude=coord[0],
                        elevation=coord[2] if len(coord) > 2 else None
                    )
                    gpx_segment.points.append(point)
                    logging.debug(f"Added point: lat={coord[1]}, lon={coord[0]}")
                except Exception as e:
                    logging.error(f"Error adding point {coord}: {str(e)}")
                    continue

            # Add metadata
            gpx.name = f"{preferences['activity_type'].title()} Route - {preferences['location']}"
            gpx.description = f"Generated route for {preferences['distance']}km {preferences['activity_type']}"
            gpx.author_name = "Route Generator"
            gpx.time = datetime.utcnow()

            xml_output = gpx.to_xml()
            logging.debug(f"Generated GPX with {len(gpx_segment.points)} points")
            return xml_output

        except Exception as e:
            logging.error(f"Failed to create GPX file: {str(e)}")
            raise Exception(f"Failed to create GPX file: {str(e)}")