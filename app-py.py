import streamlit as st
import pandas as pd
from datetime import datetime
import requests
from io import BytesIO
from PIL import Image
import base64
from pymongo import MongoClient
import os

# Configuration de la page
st.set_page_config(
    page_title="Gestion d'Inventaire",
    page_icon="📦",
    layout="wide"
)

# Connexion MongoDB
def init_db():
    conn_str = st.secrets["mongo"]["connection_string"]
    client = MongoClient(conn_str)
    return client.inventory_db

def generate_barcode_url(ean_code):
    """Génère l'URL du code-barres EAN-128"""
    ean128_code = "(01)" + ean_code
    return f"https://barcode.tec-it.com/barcode.ashx?data={ean128_code}&code=Code128&translate-esc=on", ean128_code

def get_barcode_image(url):
    """Récupère l'image du code-barres depuis l'URL"""
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return Image.open(BytesIO(response.content))
        return None
    except:
        return None

def main():
    st.title("📦 Gestion d'Inventaire")
    
    db = init_db()
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Ajout d'article")
        ean_code = st.text_input("Code EAN")
        
        if ean_code:
            barcode_url, ean128_code = generate_barcode_url(ean_code)
            barcode_image = get_barcode_image(barcode_url)
            
            if barcode_image:
                st.image(barcode_image, caption=f"Code-barres EAN-128: {ean128_code}")
                
                with st.form("inventory_form"):
                    produit = st.text_input("Produit")
                    description = st.text_input("Description")
                    quantite = st.number_input("Quantité", min_value=0)
                    localisation = st.text_input("Localisation")
                    
                    if st.form_submit_button("Ajouter à l'inventaire"):
                        new_entry = {
                            'EAN': ean_code,
                            'Produit': produit,
                            'Description': description,
                            'Quantité': quantite,
                            'Localisation': localisation,
                            'Date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        
                        # Sauvegarder l'image comme base64
                        buffered = BytesIO()
                        barcode_image.save(buffered, format="PNG")
                        img_str = base64.b64encode(buffered.getvalue()).decode()
                        
                        # Ajouter l'image à l'entrée
                        new_entry['barcode_image'] = img_str
                        
                        # Ajouter à la base de données
                        db.inventory.insert_one(new_entry)
                        st.success("Article ajouté à l'inventaire")
                        st.experimental_rerun()
    
    with col2:
        st.subheader("Inventaire")
        inventory = list(db.inventory.find({}, {'barcode_image': 0}))  # Exclure l'image pour l'affichage
        if inventory:
            df = pd.DataFrame(inventory)
            # Convertir ObjectId en string si présent
            if '_id' in df.columns:
                df['_id'] = df['_id'].astype(str)
            st.dataframe(df, use_container_width=True)
            
            # Export CSV
            csv = df.to_csv(index=False)
            st.download_button(
                "📥 Télécharger l'inventaire (CSV)",
                data=csv,
                file_name="inventaire.csv",
                mime="text/csv",
                key="download_csv"
            )
        else:
            st.info("Aucun article dans l'inventaire")

if __name__ == "__main__":
    main()
