import streamlit as st
import pandas as pd
from datetime import datetime
import requests
from io import BytesIO
from PIL import Image
from fpdf import FPDF
import base64
from pymongo import MongoClient

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

def create_pdf(ean_code, barcode_image, product_info):
    """Crée un PDF avec le code-barres et les informations du produit"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    
    # Informations du produit
    pdf.cell(0, 10, f"Code EAN: {ean_code}", ln=True)
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, f"Produit: {product_info['Produit']}", ln=True)
    pdf.cell(0, 10, f"Description: {product_info['Description']}", ln=True)
    pdf.cell(0, 10, f"Quantité: {str(product_info['Quantité'])}", ln=True)
    pdf.cell(0, 10, f"Localisation: {product_info['Localisation']}", ln=True)
    
    # Sauvegarder l'image temporairement
    temp_image = "temp_barcode.png"
    barcode_image.save(temp_image)
    
    # Ajouter l'image au PDF
    pdf.image(temp_image, x=10, y=100, w=190)
    
    # Retourner le PDF en bytes
    return pdf.output(dest='S').encode('latin-1')

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
                        
                        # Générer et afficher le PDF
                        pdf_bytes = create_pdf(ean_code, barcode_image, new_entry)
                        st.download_button(
                            "📄 Télécharger l'étiquette PDF",
                            pdf_bytes,
                            f"etiquette_{ean_code}.pdf",
                            "application/pdf"
                        )
                        
                        # Ajouter à la base de données
                        db.inventory.insert_one(new_entry)
                        st.success("Article ajouté à l'inventaire")
                        st.experimental_rerun()
    
    with col2:
        st.subheader("Inventaire")
        inventory = list(db.inventory.find({}, {'_id': 0}))
        if inventory:
            df = pd.DataFrame(inventory)
            st.dataframe(df, use_container_width=True)
            
            # Export CSV
            csv = df.to_csv(index=False)
            st.download_button(
                "📥 Télécharger l'inventaire (CSV)",
                csv,
                "inventaire.csv",
                "text/csv"
            )
        else:
            st.info("Aucun article dans l'inventaire")

if __name__ == "__main__":
    main()
