import requests
import logging
import json
import time
import random
from math import radians, cos, sin, pi
from config import ORS_API_KEY, ORS_BASE_URL, ACTIVITY_PROFILES

class ORSService:
    def __init__(self):
        self.headers = {
            'Authorization': ORS_API_KEY,
            'Content-Type': 'application/json',
            'Accept': 'application/json, application/geo+json'
        }

    def geocode_location(self, location_name, preferences=None):
        """Convertir un nom de localité en coordonnées GPS"""
        endpoint = f"{ORS_BASE_URL}/geocode/search"
        
        # Vérification de la clé API en premier
        if not ORS_API_KEY or ORS_API_KEY.strip() == "":
            logging.error("ERREUR CRITIQUE: La clé API ORS n'est pas configurée")
            raise Exception("Configuration manquante: La clé API OpenRouteService n'est pas définie dans les variables d'environnement")
            
        # Vérifier que la localité n'est pas vide
        if not location_name or location_name.strip() == "":
            logging.error("Localité vide fournie")
            raise Exception("Veuillez entrer un nom de ville ou village valide")
        
        # Normalisation du nom de la localité pour éviter les problèmes avec les tirets, etc.
        normalized_location = location_name.strip().replace("-", " ")
        logging.info(f"Localité normalisée: {normalized_location}")
        
        # Essayer plusieurs stratégies de recherche
        search_strategies = [
            # Stratégie 1: recherche directe avec code pays
            {
                'text': normalized_location,
                'size': 5,
                'layers': 'locality,borough,neighbourhood,county',
                'boundary.country': 'FRA'
            },
            # Stratégie 2: recherche précise avec Bretagne
            {
                'text': f"{normalized_location}, Bretagne, France",
                'size': 5,
                'layers': 'locality,borough,neighbourhood,county,address',
                'boundary.country': 'FRA'
            },
            # Stratégie 3: recherche géographique limitée
            {
                'text': normalized_location,
                'size': 5,
                'layers': 'locality,borough,neighbourhood,county,address',
                'boundary.country': 'FRA',
                'boundary.rect.min_lon': -5.2,  # Limites approximatives de la Bretagne
                'boundary.rect.min_lat': 47.0,
                'boundary.rect.max_lon': -0.8,
                'boundary.rect.max_lat': 49.0
            }
        ]
        
        # En dernier recours, essayer des villes connues en Bretagne
        if normalized_location.lower() == "saint-brieuc":
            logging.info("Utilisation des coordonnées prédéfinies pour Saint-Brieuc")
            return [-2.7849, 48.5134]  # Coordonnées approximatives de Saint-Brieuc
        elif normalized_location.lower() == "rennes":
            return [-1.6743, 48.1173]
        elif normalized_location.lower() == "brest":
            return [-4.4860, 48.3904] 
        elif normalized_location.lower() == "quimper":
            return [-4.0972, 47.9960]
        elif normalized_location.lower() == "vannes":
            return [-2.7600, 47.6586]
        elif normalized_location.lower() == "lorient":
            return [-3.3800, 47.7486]
            
        logging.info(f"Tentative de géocodage pour: {location_name}")
        
        # Définir les limites de la Bretagne (légèrement élargies pour inclure les zones limitrophes)
        BRETAGNE_BOUNDS = {
            'min_lat': 47.0,
            'max_lat': 49.0,
            'min_lon': -5.2,
            'max_lon': -0.8
        }
        
        last_error = None
        last_response = None
        
        # Essayer chaque stratégie jusqu'à ce qu'une réussisse
        for strategy_index, params in enumerate(search_strategies):
            try:
                logging.info(f"Essai de la stratégie {strategy_index+1} avec params: {params}")
                
                # Vérifier et afficher l'URL complète pour le débogage
                request_url = endpoint + "?" + "&".join([f"{k}={v}" for k, v in params.items()])
                logging.debug(f"URL de requête: {request_url}")
                
                # Vérifier les en-têtes
                logging.debug(f"En-têtes: Authorization: {ORS_API_KEY[:5]}...{ORS_API_KEY[-3:] if len(ORS_API_KEY) > 8 else ''}")
                
                response = requests.get(
                    endpoint,
                    headers=self.headers,
                    params=params,
                    timeout=15
                )
                
                last_response = response
                
                if response.status_code != 200:
                    logging.warning(f"Échec de la stratégie {strategy_index+1}: {response.status_code} - {response.text[:200]}")
                    last_error = f"Erreur de géocodage (code {response.status_code})"
                    continue
                
                # Vérifier si la réponse est bien du JSON
                try:
                    data = response.json()
                except json.JSONDecodeError:
                    logging.warning(f"Réponse non-JSON pour la stratégie {strategy_index+1}")
                    logging.warning(f"Contenu: {response.text[:200]}...")
                    last_error = "Format de réponse invalide"
                    continue
                
                if not data.get('features') or len(data['features']) == 0:
                    logging.warning(f"Aucun résultat pour la stratégie {strategy_index+1}")
                    last_error = "Localité non trouvée"
                    continue
                
                # Parcourir les résultats pour trouver une correspondance en Bretagne
                for feature in data['features']:
                    if 'geometry' not in feature or 'coordinates' not in feature['geometry']:
                        continue
                    
                    coordinates = feature['geometry']['coordinates']
                    lat = coordinates[1]
                    lon = coordinates[0]
                    
                    # Extraire le nom réel trouvé pour le log
                    found_name = feature.get('properties', {}).get('name', 'Localité inconnue')
                    found_region = feature.get('properties', {}).get('region', 'Région inconnue')
                    
                    # Vérifier si la localité est en Bretagne (ou à proximité)
                    in_bretagne = (
                        BRETAGNE_BOUNDS['min_lat'] <= lat <= BRETAGNE_BOUNDS['max_lat'] and
                        BRETAGNE_BOUNDS['min_lon'] <= lon <= BRETAGNE_BOUNDS['max_lon']
                    )
                    
                    logging.info(f"Résultat trouvé: {found_name}, {found_region} -> [{lon}, {lat}], En Bretagne: {in_bretagne}")
                    
                    if in_bretagne:
                        logging.info(f"Géocodage réussi: {location_name} -> {found_name}, {found_region} -> [{lon}, {lat}]")
                        return [lon, lat]  # Inverser l'ordre pour correspondre au format ORS
                    
                    # En dernier recours, prendre la première correspondance même hors Bretagne
                    if strategy_index == len(search_strategies) - 1:
                        logging.warning(f"Aucune correspondance en Bretagne, utilisation du premier résultat: {found_name}, {found_region}")
                        return [lon, lat]
                
                # Si on arrive ici, aucune correspondance n'a été trouvée en Bretagne
                logging.warning(f"Aucune correspondance en Bretagne pour la stratégie {strategy_index+1}")
                last_error = "Localité non trouvée en Bretagne"
                
            except requests.exceptions.RequestException as e:
                logging.error(f"Erreur de connexion pour la stratégie {strategy_index+1}: {str(e)}")
                last_error = f"Problème de connexion au service de géocodage: {str(e)}"
        
        # Si on arrive ici, aucune stratégie n'a fonctionné
        error_msg = last_error or "Impossible de localiser cette ville en Bretagne"
        
        # Si nous avons une réponse, enregistrer plus de détails pour le débogage
        if last_response:
            logging.error(f"Dernière réponse: Code {last_response.status_code}")
            logging.error(f"Contenu de la réponse: {last_response.text[:500]}...")
            logging.error(f"En-têtes de réponse: {dict(last_response.headers)}")
        
        # Utiliser des coordonnées de secours pour Rennes
        logging.warning("Utilisation des coordonnées par défaut pour Rennes comme solution de secours")
        return [-1.6743, 48.1173]  # Coordonnées approximatives de Rennes

    def generate_route(self, coordinates, preferences):
        """Générer un itinéraire avec des coordonnées données et des préférences"""
        # Extraction des préférences avec validation
        logging.info(f"Préférences reçues pour la génération d'itinéraire: {preferences}")
        
        # Vérifier si les préférences sont complètes
        if not preferences:
            logging.error("Préférences vides pour la génération d'itinéraire")
            raise Exception("Aucune préférence fournie pour l'itinéraire")
            
        # Extraction avec valeurs par défaut sécurisées
        try:
            activity = preferences.get('activity_type', 'hiking')
            # Assurer que la distance est un nombre valide
            distance_str = preferences.get('distance', '5')
            try:
                distance_km = float(distance_str)
                if distance_km <= 0:
                    logging.warning(f"Distance invalide: {distance_km}, utilisation de la valeur par défaut 5km")
                    distance_km = 5.0
            except (ValueError, TypeError):
                logging.warning(f"Conversion de distance échouée pour '{distance_str}', utilisation de la valeur par défaut 5km")
                distance_km = 5.0
                
            # Type de parcours (boucle ou aller-retour)
            route_type = preferences.get('route_type', 'loop')
            if route_type not in ['loop', 'roundtrip']:
                logging.warning(f"Type de parcours inconnu: {route_type}, utilisation de 'loop' par défaut")
                route_type = 'loop'
                
            # Autres préférences pour logs et potentielle utilisation future
            level = preferences.get('level', 'intermediate')
            landscape = preferences.get('landscape', 'mixed')
            elevation_preference = preferences.get('elevation_preference', 'moderate')
            surface_type = preferences.get('surface_type', 'mixed')
            
            logging.info(f"Générer un itinéraire: activité={activity}, distance={distance_km}km, type={route_type}, niveau={level}, paysage={landscape}")
            
        except Exception as e:
            logging.error(f"Erreur lors de l'extraction des préférences: {str(e)}")
            raise Exception(f"Impossible de traiter les préférences d'itinéraire: {str(e)}")

        # Sélectionner le profil approprié
        profile = ACTIVITY_PROFILES.get(activity, 'foot-hiking')
        logging.info(f"Profil ORS sélectionné: {profile}")

        # Générer l'itinéraire en fonction du type
        if route_type == 'loop':
            return self._generate_simple_loop(coordinates, profile, distance_km)
        else:
            return self._generate_simple_out_and_back(coordinates, profile, distance_km)

    def _generate_simple_loop(self, start_point, profile, distance_km):
        """Générer un itinéraire en boucle simple"""
        logging.info(f"Génération d'un itinéraire en boucle de {distance_km}km depuis {start_point}")
        
        # Facteur d'ajustement adaptatif basé sur la distance
        # Plus la distance est grande, plus le facteur est important
        if distance_km <= 3:
            adjustment_factor = 1.3  # Augmenté pour les courtes distances
        elif distance_km <= 10:
            adjustment_factor = 1.7  # Augmenté pour les distances moyennes
        else:
            adjustment_factor = 2.0  # Augmenté pour les longues distances
            
        logging.info(f"Facteur d'ajustement initial: {adjustment_factor} pour {distance_km}km")
        
        # Plusieurs tentatives pour obtenir la bonne distance
        max_attempts = 3
        best_route_data = None
        best_distance_diff = float('inf')
        
        for attempt in range(max_attempts):
            # Ajuster le facteur à chaque tentative si nécessaire
            if attempt > 0:
                # Si on a déjà un résultat, ajuster en fonction de la différence
                if best_route_data:
                    actual_distance = best_route_data['features'][0]['properties']['segments'][0]['distance'] / 1000
                    ratio = distance_km / actual_distance
                    # Limiter l'ajustement pour éviter des oscillations trop importantes
                    ratio = max(0.7, min(1.5, ratio))
                    adjustment_factor *= ratio
                    logging.info(f"Tentative {attempt+1}: Ajustement du facteur à {adjustment_factor} (ratio {ratio:.2f})")
                else:
                    # Augmenter progressivement si on n'a pas encore de résultat
                    adjustment_factor *= 1.2
            
            # Calculer le rayon approximatif pour la distance souhaitée
            # Formule ajustée: distance ≈ 2πr où r est le rayon, avec facteur d'ajustement
            radius_km = (distance_km / (2 * pi)) * adjustment_factor
            
            # Convertir le rayon en degrés (approximativement)
            # Ajustement pour la latitude: 1 degré de longitude ≈ 111km * cos(latitude)
            lat_radians = radians(start_point[1])
            lon_scale = cos(lat_radians)
            radius_lon_deg = radius_km / (111.0 * lon_scale) if lon_scale > 0.1 else radius_km / 11.1
            radius_lat_deg = radius_km / 111.0
            
            logging.info(f"Rayon calculé: {radius_km}km, {radius_lon_deg}° lon, {radius_lat_deg}° lat")
            
            # Générer des points en forme d'ellipse (pour compenser la distorsion)
            points = []
            points.append(start_point)  # Point de départ
            
            # Utiliser plus de points pour avoir un itinéraire plus naturel
            num_points = 8  # Augmenté pour plus de précision
            
            for i in range(num_points):
                angle = i * (2 * pi / num_points)
                # Utiliser une forme d'ellipse pour compenser la projection
                lon = start_point[0] + radius_lon_deg * cos(angle)
                lat = start_point[1] + radius_lat_deg * sin(angle)
                
                # Ajouter un peu de variation aléatoire (±5%), réduit pour plus de précision
                lon_jitter = radius_lon_deg * 0.05 * (random.random() - 0.5)
                lat_jitter = radius_lat_deg * 0.05 * (random.random() - 0.5)
                
                points.append([lon + lon_jitter, lat + lat_jitter])
                
            points.append(start_point)  # Retour au point de départ
            
            logging.info(f"Généré {len(points)} points pour l'itinéraire")
            
            try:
                # Essayer avec ces points
                route_data = self._request_directions(points, profile)
                
                # Vérifier la distance obtenue
                actual_distance = route_data['features'][0]['properties']['segments'][0]['distance'] / 1000
                distance_diff = abs(actual_distance - distance_km)
                difference_percent = (distance_diff / distance_km) * 100
                
                logging.info(f"Tentative {attempt+1}: Distance obtenue: {actual_distance:.2f}km " +
                           f"(différence: {distance_diff:.2f}km / {difference_percent:.1f}%)")
                
                # Enregistrer cette route si elle est meilleure que ce qu'on a déjà
                if distance_diff < best_distance_diff:
                    best_distance_diff = distance_diff
                    best_route_data = route_data
                    logging.info(f"Nouvelle meilleure route: différence de {best_distance_diff:.2f}km")
                
                # Si la différence est acceptable, arrêter les tentatives
                if difference_percent <= 15:  # Seuil de tolérance réduit à 15%
                    logging.info("Distance suffisamment proche, arrêt des tentatives")
                    return route_data
                
            except Exception as e:
                logging.warning(f"Erreur lors de la tentative {attempt+1}: {str(e)}")
        
        # Retourner la meilleure route trouvée ou la dernière tentative
        if best_route_data:
            actual_distance = best_route_data['features'][0]['properties']['segments'][0]['distance'] / 1000
            logging.info(f"Utilisation de la meilleure route trouvée: {actual_distance:.2f}km " +
                       f"(différence: {best_distance_diff:.2f}km)")
            return best_route_data
        
        # En cas d'échec total, renvoyer la dernière tentative
        logging.warning("Aucune route acceptable trouvée, renvoi du dernier résultat")
        return route_data

    def _generate_simple_out_and_back(self, start_point, profile, distance_km):
        """Générer un itinéraire aller-retour simple"""
        logging.info(f"Génération d'un itinéraire aller-retour de {distance_km}km depuis {start_point}")
        
        # Distance aller = moitié de la distance totale
        half_distance_km = distance_km / 2
        
        # Facteur d'ajustement adaptatif, augmenté pour plus de précision
        if half_distance_km <= 3:
            adjustment_factor = 1.4
        elif half_distance_km <= 10:
            adjustment_factor = 1.7
        else:
            adjustment_factor = 2.0
            
        logging.info(f"Facteur d'ajustement initial: {adjustment_factor} pour {half_distance_km}km (aller)")
        
        # Plusieurs tentatives pour obtenir la bonne distance
        max_attempts = 3
        best_route_data = None
        best_distance_diff = float('inf')
        
        for attempt in range(max_attempts):
            # Ajuster le facteur à chaque tentative si nécessaire
            if attempt > 0:
                # Si on a déjà un résultat, ajuster en fonction de la différence
                if best_route_data:
                    actual_distance = best_route_data['features'][0]['properties']['segments'][0]['distance'] / 1000
                    ratio = distance_km / actual_distance
                    # Limiter l'ajustement pour éviter des oscillations trop importantes
                    ratio = max(0.7, min(1.5, ratio))
                    adjustment_factor *= ratio
                    logging.info(f"Tentative {attempt+1}: Ajustement du facteur à {adjustment_factor} (ratio {ratio:.2f})")
                else:
                    # Augmenter progressivement si on n'a pas encore de résultat
                    adjustment_factor *= 1.2
            
            # Convertir la distance en degrés avec ajustement pour la latitude
            lat_radians = radians(start_point[1])
            lon_scale = cos(lat_radians)
            
            # Ajuster pour la distorsion aux différentes latitudes
            lon_distance_deg = (half_distance_km * adjustment_factor) / (111.0 * lon_scale) if lon_scale > 0.1 else (half_distance_km * adjustment_factor) / 11.1
            lat_distance_deg = (half_distance_km * adjustment_factor) / 111.0
            
            # Utiliser différentes directions à chaque tentative pour avoir plus de chances de succès
            if attempt == 0:
                # Première tentative: direction aléatoire mais avec des préférences régionales
                angle = random.uniform(0, 2 * pi)
                
                # Ajouter une préférence pour éviter l'océan en Bretagne occidentale
                if start_point[0] < -3.0:  # longitude ouest (Brest, etc.)
                    # Éviter de trop aller vers l'ouest (océan)
                    preferred_angles = [pi/4, 3*pi/4, 5*pi/4, 7*pi/4]  # NE, SE, SO, NO
                    angle = min(preferred_angles, key=lambda a: abs((a - angle) % (2*pi)))
            else:
                # Tentatives suivantes: directions orthogonales par rapport à la première
                angle = (angle + (pi/2) * attempt) % (2*pi)
            
            logging.info(f"Tentative {attempt+1}: Direction {angle:.2f} radians")
            
            # Calculer le point d'arrivée
            end_point = [
                start_point[0] + lon_distance_deg * cos(angle),
                start_point[1] + lat_distance_deg * sin(angle)
            ]
            
            # Créer des points intermédiaires pour un itinéraire plus naturel
            points = [start_point]
            
            # Ajouter 3 points intermédiaires (plus que précédemment)
            num_intermediates = 3
            for i in range(1, num_intermediates + 1):
                fraction = i / (num_intermediates + 1)
                intermediate_point = [
                    start_point[0] + fraction * (end_point[0] - start_point[0]),
                    start_point[1] + fraction * (end_point[1] - start_point[1])
                ]
                
                # Ajouter une légère variation pour éviter une ligne droite (réduite pour plus de précision)
                jitter_scale = 0.08 * fraction * (1 - fraction)  # Max au milieu, zéro aux extrémités
                lon_jitter = lon_distance_deg * jitter_scale * (random.random() - 0.5)
                lat_jitter = lat_distance_deg * jitter_scale * (random.random() - 0.5)
                
                intermediate_point[0] += lon_jitter
                intermediate_point[1] += lat_jitter
                
                points.append(intermediate_point)
                
            points.append(end_point)
            
            logging.info(f"Généré {len(points)} points pour l'itinéraire aller-retour")
            
            try:
                # Essayer avec ces points
                route_data = self._request_directions(points, profile)
                
                # Vérifier la distance obtenue
                actual_distance = route_data['features'][0]['properties']['segments'][0]['distance'] / 1000
                distance_diff = abs(actual_distance - distance_km)
                difference_percent = (distance_diff / distance_km) * 100
                
                logging.info(f"Tentative {attempt+1}: Distance obtenue: {actual_distance:.2f}km " +
                           f"(différence: {distance_diff:.2f}km / {difference_percent:.1f}%)")
                
                # Enregistrer cette route si elle est meilleure que ce qu'on a déjà
                if distance_diff < best_distance_diff:
                    best_distance_diff = distance_diff
                    best_route_data = route_data
                    logging.info(f"Nouvelle meilleure route: différence de {best_distance_diff:.2f}km")
                
                # Si la différence est acceptable, arrêter les tentatives
                if difference_percent <= 15:  # Seuil de tolérance réduit à 15%
                    logging.info("Distance suffisamment proche, arrêt des tentatives")
                    return route_data
                
            except Exception as e:
                logging.warning(f"Erreur lors de la tentative {attempt+1}: {str(e)}")
        
        # Retourner la meilleure route trouvée ou la dernière tentative
        if best_route_data:
            actual_distance = best_route_data['features'][0]['properties']['segments'][0]['distance'] / 1000
            logging.info(f"Utilisation de la meilleure route trouvée: {actual_distance:.2f}km " +
                       f"(différence: {best_distance_diff:.2f}km)")
            return best_route_data
        
        # En cas d'échec total, renvoyer la dernière tentative
        logging.warning("Aucune route acceptable trouvée, renvoi du dernier résultat")
        return route_data

    def _request_directions(self, points, profile):
        """Envoyer une requête à l'API Directions d'ORS"""
        endpoint = f"{ORS_BASE_URL}/directions/{profile}/geojson"

        payload = {
            'coordinates': points,
            'instructions': True,
            'language': 'fr',
            'geometry': True,
            'format': 'geojson'
        }

        logging.info(f"Envoi requête directions: {len(points)} points, profil {profile}")
        logging.debug(f"Payload: {json.dumps(payload)}")

        try:
            response = requests.post(
                endpoint,
                headers=self.headers,
                json=payload,
                timeout=20
            )

            # Vérifier le code de statut
            if response.status_code != 200:
                logging.error(f"Erreur API: {response.status_code} - {response.text[:300]}")
                raise Exception(f"Le service d'itinéraire a renvoyé une erreur (code {response.status_code})")

            # Vérifier que la réponse est du JSON
            content_type = response.headers.get('Content-Type', '')
            if 'application/json' not in content_type and 'application/geo+json' not in content_type:
                logging.error(f"Type de contenu non-JSON: {content_type}")
                logging.error(f"Contenu: {response.text[:300]}...")
                raise Exception("Le service d'itinéraire a renvoyé un format invalide")

            # Analyser la réponse
            try:
                data = response.json()

                # Vérifier la structure de base
                if 'features' not in data or not data['features']:
                    logging.error("Structure de données manquante")
                    raise Exception("Données d'itinéraire incomplètes")

                # Vérifier qu'on a bien un itinéraire
                feature = data['features'][0]
                if 'properties' not in feature or 'segments' not in feature['properties']:
                    logging.error("Propriétés d'itinéraire manquantes")
                    raise Exception("Structure d'itinéraire invalide")

                # Calculer la distance réelle
                actual_distance = feature['properties']['segments'][0]['distance'] / 1000
                logging.info(f"Itinéraire généré: {actual_distance:.2f} km")

                return data

            except json.JSONDecodeError as e:
                logging.error(f"Erreur JSON: {str(e)}")
                logging.error(f"Contenu: {response.text[:300]}")
                raise Exception("Impossible d'analyser la réponse du service d'itinéraire")

        except requests.exceptions.RequestException as e:
            logging.error(f"Erreur réseau: {str(e)}")
            raise Exception("Problème de connexion au service d'itinéraire")