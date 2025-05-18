import re
import logging
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from textblob import TextBlob
import config

# Configurar logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("fake_news_detector")

# Garantir que os recursos necessários do NLTK estejam disponíveis
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

# Lista de stopwords em português
try:
    STOPWORDS = set(nltk.corpus.stopwords.words('portuguese'))
except:
    logger.warning("Não foi possível carregar stopwords em português, usando lista vazia.")
    STOPWORDS = set()

class FakeNewsDetector:
    def __init__(self):
        self.suspicious_keywords = config.FAKE_NEWS_KEYWORDS
        self.vectorizer = TfidfVectorizer(stop_words=list(STOPWORDS))

    def check_suspicious_phrases(self, text):
        """Verifica se o texto contém frases suspeitas comuns em fake news"""
        text = text.lower()
        score = 0
        matches = []
        
        for keyword in self.suspicious_keywords:
            if keyword.lower() in text:
                score += 1
                matches.append(keyword)
        
        return score, matches
    
    def check_exclamation_marks(self, text):
        """Conta pontos de exclamação, que costumam ser excessivos em fake news"""
        count = text.count("!")
        if count > 3:
            return (count / len(text.split())) * 10  # Normalizar pela quantidade de palavras
        return 0
    
    def check_all_caps(self, text):
        """Verifica se há uso excessivo de PALAVRAS EM MAIÚSCULAS"""
        words = text.split()
        all_caps_count = sum(1 for word in words if word.isupper() and len(word) > 3)
        if all_caps_count > 0:
            return (all_caps_count / len(words)) * 10  # Normalizado pela quantidade de palavras
        return 0
    
    def check_clickbait_title(self, title):
        """Verifica se o título parece ser clickbait"""
        clickbait_patterns = [
            r"(?i)você não vai acreditar",
            r"(?i)incrível",
            r"(?i)chocante",
            r"(?i)surpreendente",
            r"(?i)impressionante",
            r"(?i)nunca imaginaria",
            r"(?i)assustador",
            r"(?i)o que aconteceu depois",
            r"(?i)\d+ (coisas|fatos|razões)",
            r"(?i)segredo",
            r"(?i)revelado",
            r"(?i)médicos odeiam",
        ]
        
        score = 0
        for pattern in clickbait_patterns:
            if re.search(pattern, title):
                score += 1
        
        return score
    
    def analyze_sentiment(self, text):
        """Analisa se o sentimento do texto é muito extremo (positivo ou negativo)"""
        blob = TextBlob(text)
        sentiment = blob.sentiment.polarity
        
        # Sentimentos extremos (muito positivo ou muito negativo) são suspeitos
        return abs(sentiment) > 0.8
    
    def evaluate_text(self, title, content):
        """Avalia o texto para determinar a probabilidade de ser fake news"""
        # Inicializar pontuação (quanto maior, mais suspeito)
        fake_score = 0
        
        # 1. Verificar palavras-chave suspeitas
        keyword_score, matches = self.check_suspicious_phrases(title + " " + content)
        fake_score += keyword_score * 2  # Peso maior para palavras-chave
        
        # 2. Verificar excesso de pontos de exclamação
        exclamation_score = self.check_exclamation_marks(title + " " + content)
        fake_score += exclamation_score
        
        # 3. Verificar uso excessivo de maiúsculas
        caps_score = self.check_all_caps(title + " " + content)
        fake_score += caps_score
        
        # 4. Verificar título clickbait
        clickbait_score = self.check_clickbait_title(title)
        fake_score += clickbait_score * 2  # Peso maior para títulos clickbait
        
        # 5. Verificar sentimento extremo
        if self.analyze_sentiment(title + " " + content):
            fake_score += 2
        
        # Calcular probabilidade (normalizada para 0-1)
        # Pontuação máxima possível considerando os pesos
        max_possible_score = len(self.suspicious_keywords) * 2 + 10 + 10 + 12 * 2 + 2
        probability = min(fake_score / 20, 1.0)  # Normaliza para um máximo razoável
        
        # Registrar o resultado
        if fake_score > 0:
            logger.info(f"Análise de fake news: Pontuação {fake_score}, Probabilidade {probability:.2f}")
            if matches:
                logger.info(f"Termos suspeitos encontrados: {', '.join(matches)}")
        
        return probability

# Função auxiliar para verificar se uma notícia é confiável
def verify_news(title, content):
    """Verifica se uma notícia é confiável para ser enviada aos usuários"""
    detector = FakeNewsDetector()
    fake_probability = detector.evaluate_text(title, content)
    
    # Se a probabilidade for maior que o limite configurado, consideramos como potencial fake news
    is_reliable = fake_probability < (1 - config.MIN_CONFIDENCE_SCORE)
    
    if not is_reliable:
        logger.warning(f"Potencial fake news detectada (pontuação: {fake_probability:.2f}): {title}")
    
    return is_reliable


# Para testes
if __name__ == "__main__":
    detector = FakeNewsDetector()
    
    # Teste com exemplo óbvio de fake news
    fake_title = "MÉDICOS ESTÃO CHOCADOS! Descoberta INCRÍVEL cura TODAS as doenças em 24h!"
    fake_content = """Você não vai acreditar no que descobrimos! Um médico REVOLUCIONÁRIO descobriu 
    uma PLANTA MILAGROSA que os grandes laboratórios ESTÃO ESCONDENDO do público!!! 
    Compartilhe AGORA antes que apaguem essa mensagem!!"""
    
    fake_probability = detector.evaluate_text(fake_title, fake_content)
    print(f"Probabilidade de fake news: {fake_probability:.2f}")
    print(f"É confiável: {verify_news(fake_title, fake_content)}")
    
    # Teste com notícia normal
    normal_title = "Pesquisadores identificam novo tratamento para diabetes tipo 2"
    normal_content = """Um estudo publicado na revista científica Nature Medicine mostrou resultados 
    promissores para um novo medicamento no tratamento de diabetes tipo 2. A pesquisa, conduzida 
    por cientistas da Universidade de São Paulo, acompanhou 300 pacientes durante dois anos."""
    
    normal_probability = detector.evaluate_text(normal_title, normal_content)
    print(f"Probabilidade de fake news: {normal_probability:.2f}")
    print(f"É confiável: {verify_news(normal_title, normal_content)}") 