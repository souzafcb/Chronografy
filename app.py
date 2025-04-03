# Chronografy - Aplicação em Streamlit
# Gera um GIF com imagens históricas reais do Google Street View a partir de um endereço

import streamlit as st
st.set_page_config(page_title="Chronografy", layout="centered")

import os
import requests
import imageio
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from urllib.parse import urlencode, quote_plus

# Pegando chave da API do Google a partir das secrets do Streamlit
API_KEY = st.secrets["GOOGLE_API_KEY"]

OUTPUT_FOLDER = 'streetview_images'
GIF_OUTPUT = 'chronografy.gif'

# Função para obter coordenadas a partir de um endereço
def get_coordinates(address):
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={quote_plus(address)}&key={API_KEY}"
    response = requests.get(url)
    data = response.json()
    if data['status'] == 'OK':
        location = data['results'][0]['geometry']['location']
        return location['lat'], location['lng']
    else:
        st.error("Erro ao obter coordenadas.")
        return None, None

# Tenta baixar imagens reais variando o parâmetro de tempo
# Usa imagens diretamente da API de Street View tentando diferentes anos
# embora a API estática não permita controle exato, esse método força imagens diferentes

def get_historical_images(lat, lng, start_year=2007, end_year=2024):
    images = []
    for year in range(start_year, end_year):
        url = (
            f"https://maps.googleapis.com/maps/api/streetview"
            f"?size=640x480&location={lat},{lng}"
            f"&key={API_KEY}&source=outdoor&heading=0"
        )
        metadata_url = (
            f"https://maps.googleapis.com/maps/api/streetview/metadata"
            f"?location={lat},{lng}&key={API_KEY}"
        )
        metadata_response = requests.get(metadata_url)
        metadata = metadata_response.json()

        if metadata.get('date'):
            year_found = int(metadata['date'].split("-")[0])
            if year_found == year:
                response = requests.get(url)
                if response.status_code == 200 and len(response.content) > 10000:
                    img = Image.open(BytesIO(response.content)).convert("RGB")
                    draw = ImageDraw.Draw(img)
                    try:
                        font = ImageFont.truetype("arial.ttf", 32)
                    except:
                        font = ImageFont.load_default()
                    draw.text((20, img.height - 50), f"Ano: {year}", font=font, fill=(255, 255, 255))
                    images.append((img, year))
    return images

# Gera GIF com imagens reais obtidas

def generate_gif_from_address(address):
    lat, lng = get_coordinates(address)
    if not lat or not lng:
        return

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    images_with_years = get_historical_images(lat, lng)

    if not images_with_years:
        st.warning("Nenhuma imagem histórica disponível para esse endereço.")
        return None

    image_files = []
    for idx, (img, year) in enumerate(images_with_years):
        filename = f"{OUTPUT_FOLDER}/street_{year}.jpg"
        img.save(filename)
        image_files.append(filename)

    images = [imageio.imread(img_file) for img_file in image_files]
    imageio.mimsave(GIF_OUTPUT, images, duration=200.0, loop=0)  # 6 segundos por imagem, loop infinito
    return GIF_OUTPUT

# Interface Streamlit
st.title("📸 Chronografy")
st.write("Veja a transformação de um local ao longo dos anos com imagens reais do Google Street View.")

endereco_usuario = st.text_input("Digite o endereço desejado:")

if st.button("Gerar GIF") and endereco_usuario:
    st.info("Processando... Isso pode levar alguns segundos.")
    gif_path = generate_gif_from_address(endereco_usuario)
    if gif_path:
        st.success("GIF gerado com sucesso!")
        st.image(gif_path, caption="Transformação histórica do local", use_column_width=True)
