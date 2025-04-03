# Chronografy - Aplicação em Streamlit
# Gera um GIF com imagens variadas do Google Street View a partir de um endereço

import streamlit as st
st.set_page_config(page_title="Chronografy", layout="centered")

import os
import requests
import imageio
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from urllib.parse import urlencode
import random

# Pegando chave da API do Google a partir das secrets do Streamlit
API_KEY = st.secrets["GOOGLE_API_KEY"]

OUTPUT_FOLDER = 'streetview_images'
GIF_OUTPUT = 'chronografy.gif'

# Função para obter coordenadas a partir de um endereço
def get_coordinates(address):
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={urlencode({'': address})[1:]}&key={API_KEY}"
    response = requests.get(url)
    data = response.json()
    if data['status'] == 'OK':
        location = data['results'][0]['geometry']['location']
        return location['lat'], location['lng']
    else:
        st.error("Erro ao obter coordenadas.")
        return None, None

# Gera variações de coordenadas e ângulos para tentar obter imagens distintas
# Atribui anos fictícios de forma sequencial para simular linha do tempo
def generate_variations(lat, lng, steps=8, start_year=2007):
    variations = []
    for i in range(steps):
        delta_lat = random.uniform(-0.00005, 0.00005)
        delta_lng = random.uniform(-0.00005, 0.00005)
        heading = (i * (360 // steps)) % 360
        year = start_year + i
        variations.append((lat + delta_lat, lng + delta_lng, heading, year))
    return variations

# Baixa imagem variada do Street View
# Inclui texto com o ano no canto inferior esquerdo
def download_street_view_image(lat, lng, heading=0, pitch=0, year=None):
    url = (
        f"https://maps.googleapis.com/maps/api/streetview"
        f"?size=640x480&location={lat},{lng}"
        f"&heading={heading}&pitch={pitch}&key={API_KEY}&source=outdoor"
    )
    response = requests.get(url)
    if response.status_code == 200:
        img = Image.open(BytesIO(response.content)).convert("RGB")
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", 60)
        except:
            font = ImageFont.load_default()
        if year:
            draw.text((20, img.height - 50), f"Ano: {year}", font=font, fill=(255, 255, 255))
        return img
    else:
        return None

# Função principal para gerar o GIF
# Tempo mais lento, animação contínua e clima suave

def generate_gif_from_address(address):
    lat, lng = get_coordinates(address)
    if not lat or not lng:
        return

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    variations = generate_variations(lat, lng, steps=10)

    image_files = []
    for idx, (vlat, vlng, heading, year) in enumerate(variations):
        img = download_street_view_image(vlat, vlng, heading, year=year)
        if img:
            filename = f"{OUTPUT_FOLDER}/street_var_{idx}.jpg"
            img.save(filename)
            image_files.append(filename)

    if image_files:
        images = [imageio.imread(img_file) for img_file in image_files]
        imageio.mimsave(GIF_OUTPUT, images, duration=200, loop=0)  # 20 segundos por imagem, loop contínuo
        return GIF_OUTPUT
    else:
        st.warning("Não foi possível gerar imagens variadas suficientes para um GIF.")
        return None

# Interface Streamlit
st.title("📸 Chronografy")
st.write("Veja a transformação de um local com diferentes ângulos e variações do Google Street View.")

endereco_usuario = st.text_input("Digite o endereço desejado:")

if st.button("Gerar GIF") and endereco_usuario:
    st.info("Processando... Isso pode levar alguns segundos.")
    gif_path = generate_gif_from_address(endereco_usuario)
    if gif_path:
        st.success("GIF gerado com sucesso!")
        st.image(gif_path, caption="Transformações e variações do ponto de vista", use_column_width=True)
