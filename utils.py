import requests
import logging
import pywhatkit as kit

log = logging.getLogger("botLegue")

def getMatchResult(partida, puuid, api_key, timeout=10):
    """Retorna True se o jogador venceu, False se perdeu, None em caso de erro."""
    url = f"https://americas.api.riotgames.com/lol/match/v5/matches/{partida}"
    try:
        response = requests.get(url, params={"api_key": api_key}, timeout=timeout)
    except requests.RequestException as exc:
        log.error("Falha de rede ao buscar partida %s: %s", partida, exc)
        return None

    if response.status_code != 200:
        log.error(
            "API da Riot retornou %s para a partida %s — body: %s",
            response.status_code, partida, response.text[:200],
        )
        return None

    try:
        data = response.json()
    except ValueError:
        log.error("Resposta não-JSON para a partida %s", partida)
        return None

    for info in data.get("info", {}).get("participants", []):
        if info.get("puuid") == puuid:
            return info.get("win")
    log.warning("puuid não encontrado nos participantes da partida %s", partida)
    return None

def createMessage(resultados, phone):
    try:
        if len(resultados) == 0:
            kit.sendwhatmsg_instantly(phone, "Vai jogar filho o bot tem que funcionar aqui", tab_close=True)
        else:
            derrotas = sum(1 for result in resultados if result is False)
            if derrotas > 1:
                kit.sendwhatmsg_instantly(phone, f"Parabéns pelas {derrotas} derrotas atuais! KKKKKKKKKKKKKK", tab_close=True)
            elif derrotas == 1:
                kit.sendwhatmsg_instantly(phone, "Parabéns pela derrota atual! kkk", tab_close=True)
            else:
                kit.sendwhatmsg_instantly(phone, "para de vencer por obséquio", tab_close=True)
        log.info("Mensagem enviada para %s", phone)
    except Exception as exc:
        log.error("Falha ao enviar mensagem no WhatsApp: %s", exc)
