import os
import json
from openai import OpenAI
from typing import Dict

class DescriptionGenerator:
    def __init__(self):
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        self.model = "gpt-4o"
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        
    def generate_description(self, route_data: Dict) -> str:
        """
        Generate a personalized route description using GPT-4o
        """
        try:
            prompt = self._create_prompt(route_data)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Tu es un expert en randonnée en Bretagne, spécialisé dans "
                            "la création de descriptions de parcours personnalisées et "
                            "engageantes. Utilise un ton chaleureux et professionnel."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error generating description: {str(e)}")
            return None
            
    def _create_prompt(self, route_data: Dict) -> str:
        """Create a detailed prompt for GPT-4o"""
        return f"""
        Crée une description engageante et personnalisée pour ce parcours en Bretagne :

        Détails du parcours :
        - Lieu de départ : {route_data['start_location']}
        - Type d'activité : {route_data['activity_type']}
        - Niveau : {route_data['experience_level']}
        - Distance : {route_data['distance_km']} km
        - Dénivelé : {route_data.get('elevation_gain', 'N/A')} m
        - Type de paysage : {route_data['landscape_type']}
        - Points d'intérêt : {route_data.get('points_of_interest', 'N/A')}
        - Type de parcours : {route_data['route_type']}
        - Durée estimée : {route_data['estimated_duration']}

        La description doit :
        1. Être chaleureuse et encourageante
        2. Mettre en valeur les points forts du parcours
        3. Inclure des conseils adaptés au niveau du randonneur
        4. Mentionner les points d'intérêt spécifiques
        5. Donner des informations pratiques sur le terrain et la difficulté

        Format souhaité :
        - Un paragraphe d'introduction personnalisé
        - Une description du parcours et de ses points forts
        - Des conseils pratiques
        - Une conclusion encourageante
        """
