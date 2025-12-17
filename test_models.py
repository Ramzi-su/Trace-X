import google.generativeai as genai
import os

# Remplacez par votre clé si elle n'est pas dans les variables d'environnement
api_key = os.environ.get('GOOGLE_API_KEY') 
if not api_key:
    api_key = input("Entrez votre clé API : ")

genai.configure(api_key=api_key)

print("--- Modèles disponibles pour votre script ---")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(f"Erreur critique : {e}")