import requests
from dotenv import load_dotenv
import os
import json
import logging
import sys
from utils import getMatchResult, createMessage
import time

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("botLegue")

CACHE_FILE = "partidas_cache.json"
POLL_INTERVAL_SECONDS = 300
RETRY_INTERVAL_SECONDS = 60

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def riot_get(url, params, timeout=10):
    """GET na API da Riot com tratamento de erro. Retorna o JSON ou None em caso de falha."""
    try:
        response = requests.get(url, params=params, timeout=timeout)
    except requests.RequestException as exc:
        log.error("Falha de rede ao chamar %s: %s", url, exc)
        return None

    if response.status_code != 200:
        log.error(
            "API da Riot retornou %s em %s — body: %s",
            response.status_code, url, response.text[:200],
        )
        return None

    try:
        return response.json()
    except ValueError:
        log.error("Resposta não-JSON em %s", url)
        return None

def fetch_puuid(user_name, user_tag, api_key):
    url = f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{user_name}/{user_tag}"
    data = riot_get(url, params={"api_key": api_key})
    if not data or "puuid" not in data:
        return None
    return data["puuid"]

def fetch_recent_matches(puuid, api_key, count=5):
    url = f"https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids"
    return riot_get(url, params={"api_key": api_key, "start": 0, "count": count})

def is_in_game(puuid, api_key, platform):
    """Retorna True se o jogador estiver em partida ativa agora."""
    url = f"https://{platform}.api.riotgames.com/lol/spectator/v5/active-games/by-summoner/{puuid}"
    try:
        response = requests.get(url, params={"api_key": api_key}, timeout=10)
    except requests.RequestException as exc:
        log.warning("Não foi possível verificar partida ativa: %s", exc)
        return False
    return response.status_code == 200

def main():
    user_name = os.getenv("USER_NAME")
    user_tag = os.getenv("USER_TAG")
    api_key = os.getenv("RIOT_KEY")
    user_phone = os.getenv("USER_PHONE")
    platform = os.getenv("USER_PLATFORM", "br1").lower()

    if not all([user_name, user_tag, api_key, user_phone]):
        log.error("Variáveis de ambiente faltando. Confira o .env (USER_NAME, USER_TAG, RIOT_KEY, USER_PHONE).")
        sys.exit(1)

    if not user_phone.startswith("+"):
        log.error("USER_PHONE deve incluir o código do país (ex: +5511999999999).")
        sys.exit(1)

    log.info("Buscando puuid de %s#%s", user_name, user_tag)
    puuid = fetch_puuid(user_name, user_tag, api_key)
    if not puuid:
        log.error("Não foi possível obter o puuid. Encerrando.")
        sys.exit(1)
    log.info("puuid obtido com sucesso")

    is_first_run = not os.path.exists(CACHE_FILE)
    partidas_cache = load_cache()
    log.info("Cache carregado com %d partidas conhecidas", len(partidas_cache))

    while True:
        if "PyWhatKit_DB.txt" in os.listdir():
            os.remove("PyWhatKit_DB.txt")

        partidas = fetch_recent_matches(puuid, api_key)
        if partidas is None:
            log.warning("Falha ao buscar partidas — tentando de novo em %ds", RETRY_INTERVAL_SECONDS)
            time.sleep(RETRY_INTERVAL_SECONDS)
            continue

        if is_first_run:
            log.info("Primeira execução — inicializando cache")
            partidas_cache.extend(partidas)
            save_cache(partidas_cache)
            is_first_run = False
            if is_in_game(puuid, api_key, platform):
                log.info("Jogador já está em partida — mensagem suprimida")
            else:
                createMessage([], user_phone)
            time.sleep(POLL_INTERVAL_SECONDS)
            continue

        novas_partidas = [p for p in partidas if p not in partidas_cache]

        if not novas_partidas:
            log.info("Nenhuma partida nova")
            #if not is_in_game(puuid, api_key, platform):
            #    createMessage([], user_phone)
        else:
            log.info("Encontradas %d partidas novas", len(novas_partidas))
            partidas_cache.extend(novas_partidas)
            save_cache(partidas_cache)

            resultados = []
            for partida in novas_partidas:
                resultado = getMatchResult(partida, puuid, api_key)
                if resultado is None:
                    log.warning("Não foi possível obter resultado da partida %s", partida)
                    continue
                resultados.append(resultado)

            log.info("Resultados: %s", resultados)
            #createMessage(resultados, user_phone)

        time.sleep(POLL_INTERVAL_SECONDS)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log.info("Encerrado pelo usuário")
