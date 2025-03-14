
import logging
from services.openai_service import generate_route_description
from services.ors_service import ORSService
from services.gpx_service import GPXService
from services.email_service import EmailService
import json

class RouteGeneratorService:
    def __init__(self):
        self.ors_service = ORSService()
        self.gpx_service = GPXService()
        self.email_service = EmailService()
    
    def process_user_preferences(self, user_preferences):
        """Traitement centralisé des préférences utilisateur"""
        logging.info(f"Traitement des préférences: {user_preferences}")
        
        # 1. Validation et normalisation des préférences
        normalized_preferences = self._normalize_preferences(user_preferences)
        
        # 2. Géocodage de la localisation
        coordinates = self.ors_service.geocode_location(normalized_preferences['location'])
        logging.info(f"Coordonnées obtenues: {coordinates}")
        
        # 3. Génération de l'itinéraire via ORS
        route_data = self.ors_service.generate_route(coordinates, normalized_preferences)
        
        # 4. Vérification de la distance obtenue
        actual_distance = route_data['features'][0]['properties']['segments'][0]['distance'] / 1000
        logging.info(f"Distance obtenue: {actual_distance}km (demandée: {normalized_preferences['distance']}km)")
        
        # 5. Génération de la description via OpenAI
        route_description_json = generate_route_description(normalized_preferences)
        route_description = json.loads(route_description_json)
        
        # 6. Création du fichier GPX
        gpx_content = self.gpx_service.create_gpx(route_data, normalized_preferences)
        
        # 7. Envoi de l'email avec le fichier GPX
        self.email_service.send_gpx_email(
            normalized_preferences['email'],
            gpx_content,
            route_description,
            normalized_preferences
        )
        
        return {
            'success': True,
            'distance': f"{actual_distance:.1f}km",
            'location': normalized_preferences['location']
        }
    
    def _normalize_preferences(self, preferences):
        """Normalisation des préférences utilisateur"""
        normalized = preferences.copy()
        
        # Normaliser le type de route
        if 'route_type' not in normalized or normalized['route_type'] not in ['loop', 'roundtrip']:
            normalized['route_type'] = 'loop'
            
        # Valider la distance
        try:
            distance = float(normalized['distance'])
            if distance <= 0:
                normalized['distance'] = '5'
        except (ValueError, TypeError):
            normalized['distance'] = '5'
            
        # Normaliser le niveau
        if normalized.get('level') not in ['beginner', 'intermediate', 'advanced']:
            normalized['level'] = 'intermediate'
            
        return normalized
