import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurações de API e serviços
WHATSAPP_API_KEY = os.getenv("WHATSAPP_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

# Fontes de notícias confiáveis (URLs de RSS feeds)
NEWS_SOURCES = {
    "geral": [
        "https://g1.globo.com/rss/g1/",
        "https://rss.uol.com.br/feed/noticias.xml",
        "https://feeds.folha.uol.com.br/emcimadahora/rss091.xml"
    ],
    "saude": [
        "https://g1.globo.com/rss/g1/ciencia-e-saude/",
        "https://rss.uol.com.br/feed/noticias/saude.xml"
    ],
    "tecnologia": [
        "https://g1.globo.com/rss/g1/tecnologia/",
        "https://rss.uol.com.br/feed/noticias/tecnologia.xml"
    ],
    "economia": [
        "https://g1.globo.com/rss/g1/economia/",
        "https://rss.uol.com.br/feed/economia.xml"
    ]
}

# Palavras-chave para detecção básica de fake news
FAKE_NEWS_KEYWORDS = [
    "cura milagrosa",
    "médicos não querem que você saiba",
    "segredo revelado",
    "ganhe dinheiro rápido",
    "compartilhe antes que apaguem",
    "a mídia está escondendo",
    "descoberta revolucionária",
    "conspiração",
    "100% comprovado",
    "eles não querem que você saiba"
]

# Frases de contextualização para idosos
INTRO_MESSAGES = [
    "Bom dia! Aqui estão as notícias mais importantes para você hoje:",
    "Olá! Separamos algumas notícias confiáveis para você se manter informado(a):",
    "Tudo bem? Estas são as principais notícias de hoje que podem interessar você:",
    "Boa tarde! Selecionamos com cuidado estas notícias para manter você atualizado(a):"
]

# Configurações de envio
DEFAULT_SEND_TIME = "08:00"  # Horário padrão para envio de notícias
MAX_NEWS_PER_DAY = 10  # Número máximo de notícias por dia
MIN_CONFIDENCE_SCORE = 0.7  # Pontuação mínima de confiança para enviar uma notícia

# Configurações do sistema
DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
CACHE_DIR = os.path.join(DATA_DIR, "cache")

# Criar diretórios necessários se não existirem
for directory in [DATA_DIR, CACHE_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory) 