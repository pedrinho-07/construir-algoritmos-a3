import os
import requests
from dotenv import load_dotenv
from folium import Map, Marker, Popup, Icon

load_dotenv(".env")

BASE_URL = "http://api.olhovivo.sptrans.com.br/v2.1"

TERMO_LINHA = "8000"


def autenticar():
    s = requests.Session()
    res = s.post(f"{BASE_URL}/Login/Autenticar?token={os.getenv('SPTRANS_TOKEN')}")
    if res.text.strip().lower() != "true":
        raise RuntimeError("Falha na autenticação. Verifique o token no .env")
    return s


def buscar_linha(s, termo):
    res = s.get(f"{BASE_URL}/Linha/Buscar", params={"termosBusca": termo})
    linhas = res.json()
    if not linhas:
        raise RuntimeError(f"Nenhuma linha encontrada para '{termo}'")
    return linhas[0]  # pega a primeira correspondência


def buscar_paradas(s, codigo_linha):
    res = s.get(
        f"{BASE_URL}/Parada/BuscarParadasPorLinha",
        params={"codigoLinha": codigo_linha},
    )
    return res.json()


def buscar_posicoes(s, codigo_linha):
    res = s.get(f"{BASE_URL}/Posicao/Linha", params={"codigoLinha": codigo_linha})
    return res.json().get("vs", [])


def criar_mapa(linha, paradas, onibus):
    # Centraliza no primeiro ponto disponível
    if onibus:
        centro = [onibus[0]["py"], onibus[0]["px"]]
    elif paradas:
        centro = [paradas[0]["py"], paradas[0]["px"]]
    else:
        centro = [-23.5505, -46.6333]  # centro de São Paulo

    m = Map(location=centro, zoom_start=13)

    # Paradas: pins AZUIS
    for p in paradas:
        Marker(
            location=[p["py"], p["px"]],
            popup=Popup(f"Parada: {p['np']}<br>{p['ed']}", max_width=250),
            icon=Icon(color="blue", icon="info-sign"),
        ).add_to(m)

    # Ônibus em tempo real: pins VERMELHOS
    for o in onibus:
        Marker(
            location=[o["py"], o["px"]],
            popup=Popup(
                f"Ônibus prefixo {o['p']}<br>Atualizado: {o['ta']}", max_width=250
            ),
            icon=Icon(color="red", icon="bus", prefix="fa"),
        ).add_to(m)

    return m


def main():
    s = autenticar()
    linha = buscar_linha(s, TERMO_LINHA)
    codigo = linha["cl"]
    print(f"Linha: {linha['lt']}-{linha['tl']} ({linha['tp']} -> {linha['ts']})")

    paradas = buscar_paradas(s, codigo)
    onibus = buscar_posicoes(s, codigo)
    print(f"{len(paradas)} paradas | {len(onibus)} ônibus em circulação")

    m = criar_mapa(linha, paradas, onibus)
    m.save("mapa_onibus.html")
    print("Mapa salvo em mapa_onibus.html")


if __name__ == "__main__":
    main()