from flask import render_template, request, jsonify
from app import app
from services.route_generator import RouteGenerator
from services.location_validator import LocationValidator
from services.description_generator import DescriptionGenerator
from services.email_service import EmailService
import logging

# Initialize services
route_generator = RouteGenerator()
location_validator = LocationValidator()
description_generator = DescriptionGenerator()
email_service = EmailService()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate-route', methods=['POST'])
def generate_route():
    try:
        data = request.json
        logging.debug(f"Received route generation request with data: {data}")

        # Validate input
        required_fields = ['location', 'activity_type', 'level', 'distance', 
                         'landscape', 'email']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400

        # Validate location is in Brittany
        location_result = location_validator.validate_brittany_location(data['location'])
        if not location_result:
            return jsonify({'error': 'Location not found or not in Brittany'}), 400
        if not location_result.is_in_brittany:
            return jsonify({'error': 'Location must be in Brittany'}), 400

        # Generate route
        route_data = route_generator.generate_route(
            (location_result.latitude, location_result.longitude),
            data
        )
        if not route_data:
            return jsonify({'error': 'Failed to generate route'}), 500

        # Generate description
        description = description_generator.generate_description({
            'start_location': data['location'],
            'activity_type': data['activity_type'],
            'experience_level': data['level'],
            'distance_km': data['distance'],
            'landscape_type': data['landscape'],
            'route_type': data.get('route_type', 'loop'),
            'elevation_gain': route_data.get('elevation_gain'),
            'points_of_interest': data.get('points_of_interest'),
            'estimated_duration': data.get('duration', '1h')
        })

        # Send email with GPX file
        try:
            email_service.send_gpx_email(
                data['email'],
                route_data['gpx_content'],
                description,
                {
                    'distance': data['distance'],
                    'activity_type': data['activity_type']
                }
            )
        except Exception as e:
            logging.error(f"Failed to send email: {str(e)}")
            return jsonify({'error': 'Failed to send email'}), 500

        return jsonify({
            'success': True,
            'message': 'Route generated and sent successfully',
            'details': {
                'distance': route_data['distance'],
                'elevation_gain': route_data.get('elevation_gain'),
                'location': data['location']
            }
        })

    except Exception as e:
        logging.error(f"Error generating route: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api-diagnostics', methods=['GET'])
def api_diagnostics():
    """Tester la connectivité avec l'API ORS"""
    results = {
        "environment": {},
        "ors_api": {
            "configuration": {},
            "connectivity": {}
        }
    }
    
    # Vérifier la configuration
    results["environment"]["replit_env"] = "REPLIT_DB_URL" in os.environ
    
    # Vérifier la clé API
    if ORS_API_KEY:
        masked_key = f"{ORS_API_KEY[:5]}...{ORS_API_KEY[-3:]}" if len(ORS_API_KEY) > 8 else "[INVALID]"
        results["ors_api"]["configuration"]["key_set"] = True
        results["ors_api"]["configuration"]["key_format"] = masked_key
        results["ors_api"]["configuration"]["key_length"] = len(ORS_API_KEY)
        results["ors_api"]["configuration"]["starts_with_standard_prefix"] = ORS_API_KEY.startswith("5b3ce3597851")
    else:
        results["ors_api"]["configuration"]["key_set"] = False
    
    # Tester l'API
    test_url = f"{ORS_BASE_URL}/geocode/search"
    
    try:
        headers = {
            'Authorization': ORS_API_KEY,
            'Accept': 'application/json'
        }
        params = {
            'text': 'Rennes, France',
            'size': 1,
            'boundary.country': 'FRA'
        }
        
        response = requests.get(test_url, headers=headers, params=params, timeout=10)
        
        results["ors_api"]["connectivity"]["status_code"] = response.status_code
        results["ors_api"]["connectivity"]["response_type"] = response.headers.get('Content-Type')
        
        if response.status_code == 200:
            results["ors_api"]["connectivity"]["success"] = True
            results["ors_api"]["connectivity"]["first_bytes"] = response.text[:50] + "..."
            try:
                data = response.json()
                results["ors_api"]["connectivity"]["is_json"] = True
                results["ors_api"]["connectivity"]["has_features"] = "features" in data and len(data["features"]) > 0
            except:
                results["ors_api"]["connectivity"]["is_json"] = False
        else:
            results["ors_api"]["connectivity"]["success"] = False
            results["ors_api"]["connectivity"]["error"] = response.text[:200]
    except Exception as e:
        results["ors_api"]["connectivity"]["success"] = False
        results["ors_api"]["connectivity"]["exception"] = str(e)
    
    return jsonify(results)

@app.route('/test-ors-api', methods=['GET'])
def test_ors_api():
    """Test route to verify ORS API is responding correctly."""
    results = {}
    
    # Option pour spécifier une ville à tester
    test_location = request.args.get('location', 'Rennes')
    
    try:
        # Test de l'API key
        key_info = "Non définie"
        if ORS_API_KEY:
            key_info = f"{ORS_API_KEY[:5]}...{ORS_API_KEY[-3:] if len(ORS_API_KEY) > 8 else ''}"
        results['api_key'] = {
            'status': 'configured' if ORS_API_KEY else 'missing',
            'format': key_info
        }
        
        # Test du géocodage
        logging.info(f"Test de géocodage pour: {test_location}")
        try:
            coordinates = ors_service.geocode_location(test_location, {'distance': '5'})
            results['geocoding'] = {
                'status': 'success',
                'location': test_location,
                'coordinates': coordinates
            }
            
            # Test de génération d'itinéraire simple
            try:
                sample_preferences = {
                    'activity_type': 'hiking',
                    'distance': '5',
                    'route_type': 'loop'
                }
                
                route_data = ors_service.generate_route(coordinates, sample_preferences)
                
                # Vérifier la validité de la réponse
                if isinstance(route_data, dict) and 'features' in route_data:
                    distance = route_data['features'][0]['properties']['segments'][0]['distance'] / 1000
                    
                    results['route_generation'] = {
                        'status': 'success',
                        'distance_km': round(distance, 2),
                        'has_geometry': 'geometry' in route_data['features'][0]
                    }
                else:
                    results['route_generation'] = {
                        'status': 'error',
                        'message': 'Format de données invalide',
                        'data_preview': str(route_data)[:100] + '...'
                    }
            except Exception as e:
                results['route_generation'] = {
                    'status': 'error',
                    'message': str(e)
                }
                
        except Exception as e:
            results['geocoding'] = {
                'status': 'error',
                'location': test_location,
                'message': str(e)
            }
            # Ne pas tester la génération d'itinéraire si le géocodage échoue
            results['route_generation'] = {
                'status': 'skipped',
                'message': 'Test ignoré car le géocodage a échoué'
            }
        
        # Vérifier d'autres villes bretonnes connues
        test_cities = ['Saint-Brieuc', 'Brest', 'Quimper', 'Vannes', 'Lorient']
        city_tests = []
        
        for city in test_cities:
            if city == test_location:
                continue  # Éviter de tester deux fois la même ville
                
            try:
                coords = ors_service.geocode_location(city)
                city_tests.append({
                    'city': city,
                    'status': 'success',
                    'coordinates': coords
                })
            except Exception as e:
                city_tests.append({
                    'city': city,
                    'status': 'error',
                    'message': str(e)
                })
        
        results['additional_cities_test'] = city_tests
        
        # Déterminer le statut global
        overall_status = 'success'
        overall_message = 'Tous les tests ont réussi'
        
        if results.get('geocoding', {}).get('status') != 'success':
            overall_status = 'error'
            overall_message = f"Le géocodage a échoué pour {test_location}"
        elif results.get('route_generation', {}).get('status') != 'success':
            overall_status = 'error'
            overall_message = "La génération d'itinéraire a échoué"
        
        results['status'] = overall_status
        results['message'] = overall_message
        
        status_code = 200 if overall_status == 'success' else 500
        return jsonify(results), status_code
            
    except Exception as e:
        logging.error(f"Erreur inattendue lors du test de l'API ORS: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Erreur inattendue lors du test: {str(e)}',
            'partial_results': results
        }), 500
from services.openai_service import generate_route_description
from services.ors_service import ORSService
from services.gpx_service import GPXService
from config import ORS_API_KEY, ORS_BASE_URL
import json
import logging
import requests
import os

ors_service = ORSService()
gpx_service = GPXService()
email_service = EmailService()