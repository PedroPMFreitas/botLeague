# botLegue

Bot que monitora as partidas de um jogador de League of Legends pela API da Riot e envia uma mensagem zoeira no WhatsApp (via PyWhatKit) sempre que detecta novas partidas — com piadas diferentes pra vitória e derrota.

## Como funciona

1. Consulta a conta da Riot pelo `USER_NAME#USER_TAG` e pega o `puuid` do jogador.
2. A cada 10 minutos, busca as 5 últimas partidas do jogador.
3. Compara com o cache da execução anterior pra identificar partidas novas.
4. Pra cada partida nova, descobre se o jogador venceu ou perdeu.
5. Manda uma mensagem no WhatsApp com base no número de derrotas.

## Pré-requisitos

- Python 3.10+
- Conta na [Riot Developer Portal](https://developer.riotgames.com/) pra gerar uma API key (a chave de desenvolvimento expira a cada 24h).
- WhatsApp Web logado no navegador padrão da máquina (PyWhatKit abre o WhatsApp Web pra mandar a mensagem).

## Instalação

```powershell
git clone <este-repo>
cd botLegue
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Configuração

Crie um arquivo `.env` na raiz do projeto baseado no `.env.example`:

```
RIOT_KEY=RGAPI-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
USER_NAME=SeuNick
USER_TAG=BR1
USER_PHONE=+5511999999999
```

- `RIOT_KEY`: sua API key da Riot.
- `USER_NAME`: nick do invocador (sem o `#`).
- `USER_TAG`: a tag depois do `#` (ex.: `BR1`).
- `USER_PHONE`: número do destinatário no formato internacional (`+55...`).

## Mensagens enviadas

| Situação | Mensagem |
|---|---|
| **Primeira execução** (sem cache) e jogador **fora de partida** | `"Vai jogar filho o bot tem que funcionar aqui"` |
| **Primeira execução** e jogador **em partida ativa** | *(mensagem suprimida)* |
| Nenhuma partida nova desde o último ciclo | `"Vai jogar filho o bot tem que funcionar aqui"` *(comentado por padrão)* |
| 1 derrota nas partidas novas | `"Parabéns pela derrota atual! kkk"` |
| 2 ou mais derrotas nas partidas novas | `"Parabéns pelas X derrotas atuais! KKKKKKKKKKKKKK"` |
| Apenas vitórias nas partidas novas | `"para de vencer por obséquio"` |

Na primeira execução o bot consulta a **Spectator API** da Riot pra ver se o jogador está em partida ativa — se estiver, a mensagem é suprimida. O bot analisa **somente as partidas novas** detectadas em cada ciclo — não o histórico completo.

## Como o WhatsApp é usado

O PyWhatKit **não tem conta própria** — ele usa o **WhatsApp Web aberto no navegador padrão da máquina** que está rodando o script.

- **Quem manda**: a conta do WhatsApp que estiver logada no WhatsApp Web do seu navegador (ou seja, a sua conta).
- **Para quem**: o número definido em `USER_PHONE` no `.env`.

Antes de rodar, certifique-se de que o WhatsApp Web está logado. O PyWhatKit vai abrir o navegador automaticamente e disparar a mensagem por lá.

## Como executar

```powershell
python league_loss.py
```

O bot vai rodar em loop — buscando partidas a cada 10 minutos. Pare com `Ctrl+C`.

> Atenção: as chamadas que enviam mensagem no WhatsApp estão **comentadas** em [league_loss.py](league_loss.py). Descomente as linhas `#createMessage(...)` quando quiser ativar o envio real. Enquanto comentadas, o script só imprime os resultados no console.

## Estrutura de arquivos

```
botLeague/
├── league_loss.py        # ponto de entrada — loop principal do bot
├── utils.py              # funções auxiliares (API e WhatsApp)
├── .env.example          # template do .env
├── partidas_cache.json   # gerado automaticamente na primeira execução
├── requirements.txt      # dependências Python
└── .gitignore
```

### league_loss.py

Contém toda a lógica de orquestração:

- **`riot_get()`** — wrapper de chamadas à API da Riot com tratamento de erro, timeout e checagem de status HTTP.
- **`fetch_puuid()`** — busca o identificador único do jogador pelo nick e tag.
- **`fetch_recent_matches()`** — retorna os IDs das últimas partidas do jogador.
- **`is_in_game()`** — consulta a Spectator API pra saber se o jogador está em partida agora.
- **`main()`** — inicializa tudo e roda o loop de polling.

### utils.py

- **`getMatchResult()`** — dado o ID de uma partida e o puuid do jogador, retorna `True` (vitória), `False` (derrota) ou `None` (erro).
- **`createMessage()`** — decide qual mensagem mandar com base nos resultados e envia via PyWhatKit no WhatsApp Web.

## Cache

O bot salva as partidas já processadas em `partidas_cache.json` na raiz do projeto. Esse arquivo é criado automaticamente na primeira execução e é ignorado pelo git. Se quiser "resetar" o estado (reprocessar tudo), é só deletar.

## Licença

Uso pessoal / brincadeira entre amigos.
