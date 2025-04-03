# Chronografy - Aplicação em Streamlit
# Gera um GIF com imagens históricas do Google Street View de um endereço

import os
import requests
import imageio
from io import BytesIO
from PIL import Image
from urllib.parse import urlencode
import streamlit as st

# Pegando chave da API do Google a partir das secrets do Streamlit
API_KEY = st.secrets["GOOGLE_API_KEY"]

OUTPUT_FOLDER = 'streetview_images'
GIF_OUTPUT = 'chronografy.gif'

# Função para obter coordenadas a partir de um endereço
def get_coordinates(address):
    url = f"https://maps.googleapis.com/maps/api/geocode/json?{urlencode({'address': address})}&key={API_KEY}"
    response = requests.get(url)
    data = response.json()
    if data['status'] == 'OK':
        location = data['results'][0]['geometry']['location']
        return location['lat'], location['lng']
    else:
        st.error("Erro ao obter coordenadas.")
        return None, None

# Função para buscar anos disponíveis (estimativa via tentativa por timestamps)
def get_available_dates(lat, lng):
    years = []
    for year in range(2007, 2024):
        timestamp_url = (
            f"https://maps.googleapis.com/maps/api/streetview"
            f"?size=640x480&location={lat},{lng}"
            f"&key={API_KEY}&source=outdoor&timestamp={year}-01"
        )
        resp = requests.get(timestamp_url)
        if resp.status_code == 200:
            if resp.content and len(resp.content) > 10000:
                years.append(year)
    return years

# Função para baixar imagem de um ano específico
def download_street_view_image(lat, lng, year, heading=0, pitch=0):
    url = (
        f"https://maps.googleapis.com/maps/api/streetview"
        f"?size=640x480&location={lat},{lng}"
        f"&heading={heading}&pitch={pitch}&key={API_KEY}&source=outdoor&timestamp={year}-01"
    )
    response = requests.get(url)
    if response.status_code == 200:
        return Image.open(BytesIO(response.content))
    else:
        st.warning(f"Erro ao baixar imagem de {year}: {response.status_code}")
        return None

# Função principal para gerar o GIF
def generate_gif_from_address(address):
    lat, lng = get_coordinates(address)
    if not lat or not lng:
        return

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    available_years = get_available_dates(lat, lng)

    image_files = []
    for year in available_years:
        img = download_street_view_image(lat, lng, year)
        if img:
            filename = f"{OUTPUT_FOLDER}/street_{year}.jpg"
            img.save(filename)
            image_files.append(filename)

    if image_files:
        images = [imageio.imread(img_file) for img_file in image_files]
        imageio.mimsave(GIF_OUTPUT, images, duration=1.5)
        return GIF_OUTPUT
    else:
        st.warning("Nenhuma imagem disponível para gerar o GIF.")
        return None

# Interface Streamlit
st.set_page_config(page_title="Chronografy", layout="centered")
st.title("📸 Chronografy")
st.write("Veja a transformação de um local ao longo dos anos com imagens do Google Street View.")

endereco_usuario = st.text_input("Digite o endereço desejado:")

if st.button("Gerar GIF") and endereco_usuario:
    st.info("Processando... Isso pode levar alguns segundos.")
    gif_path = generate_gif_from_address(endereco_usuario)
    if gif_path:
        st.success("GIF gerado com sucesso!")
        st.image(gif_path, caption="Transformações ao longo dos anos", use_column_width=True)
