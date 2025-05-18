import feedparser
import requests
from bs4 import BeautifulSoup
from newspaper import Article
import pandas as pd
import time
import random
import os
import json
import logging
from datetime import datetime, timedelta
from textblob import TextBlob
import nltk
from fake_news_detector import verify_news
import config

# Configurar logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("news_fetcher")

# Garantir que os pacotes nltk necessários estejam instalados
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    logger.info("Baixando recursos do NLTK...")
    nltk.download('punkt')


class NewsFetcher:
    def __init__(self):
        self.cache_file = os.path.join(config.CACHE_DIR, "news_cache.json")
        self.user_prefs_file = os.path.join(config.DATA_DIR, "user_preferences.json")
        self.cache = self._load_cache()
        self.user_preferences = self._load_user_preferences()
        
    def _load_cache(self):
        """Carrega o cache de notícias já processadas"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Erro ao carregar cache: {e}")
                return {"last_update": "", "processed_urls": []}
        return {"last_update": "", "processed_urls": []}
    
    def _save_cache(self):
        """Salva o cache de notícias processadas"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Erro ao salvar cache: {e}")
    
    def _load_user_preferences(self):
        """Carrega as preferências do usuário"""
        if os.path.exists(self.user_prefs_file):
            try:
                with open(self.user_prefs_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Erro ao carregar preferências do usuário: {e}")
                return {}
        return {}
    
    def fetch_news_by_category(self, category, limit=10):
        """Busca notícias por categoria especificada"""
        if category not in config.NEWS_SOURCES:
            logger.warning(f"Categoria não encontrada: {category}")
            return []
        
        all_news = []
        sources = config.NEWS_SOURCES[category]
        
        for source_url in sources:
            try:
                logger.info(f"Buscando notícias de: {source_url}")
                feed = feedparser.parse(source_url)
                
                for entry in feed.entries[:limit]:
                    if entry.link in self.cache["processed_urls"]:
                        continue
                    
                    try:
                        article_data = self._process_article(entry.link)
                        if article_data and verify_news(article_data["title"], article_data["content"]):
                            all_news.append(article_data)
                    except Exception as e:
                        logger.error(f"Erro ao processar artigo {entry.link}: {e}")
                
                # Aguardar um pouco para não sobrecarregar o servidor
                time.sleep(1)
            
            except Exception as e:
                logger.error(f"Erro ao buscar notícias de {source_url}: {e}")
        
        return all_news
    
    def _process_article(self, url):
        """Processa um artigo de notícia, extraindo seu conteúdo"""
        try:
            article = Article(url)
            article.download()
            article.parse()
            
            # Extrair data de publicação, usar data atual se não disponível
            if article.publish_date:
                pub_date = article.publish_date
            else:
                pub_date = datetime.now()
            
            # Analisar sentimento do texto (simplificado)
            if article.text:
                blob = TextBlob(article.text)
                sentiment = blob.sentiment.polarity
            else:
                sentiment = 0
            
            # Extrair imagem principal, se disponível
            image_url = article.top_image if article.top_image else ""
            
            # Criar resumo se o artigo tiver conteúdo
            summary = ""
            if article.text:
                article.nlp()
                summary = article.summary
            
            data = {
                "title": article.title,
                "url": url,
                "content": article.text,
                "summary": summary,
                "image_url": image_url,
                "published_date": pub_date.isoformat(),
                "source": article.source_url if article.source_url else url.split('/')[2],
                "sentiment": sentiment,
                "categories": article.meta_keywords if article.meta_keywords else []
            }
            
            # Adicionar à lista de URLs processados
            self.cache["processed_urls"].append(url)
            if len(self.cache["processed_urls"]) > 1000:  # Limitar tamanho do cache
                self.cache["processed_urls"] = self.cache["processed_urls"][-1000:]
            self.cache["last_update"] = datetime.now().isoformat()
            self._save_cache()
            
            return data
            
        except Exception as e:
            logger.error(f"Erro ao processar artigo de {url}: {e}")
            return None
    
    def get_news_for_user(self, user_id, count=5):
        """Obtém notícias personalizadas para um usuário específico"""
        # Verificar se o usuário tem preferências
        user_prefs = self.user_preferences.get(str(user_id), {})
        
        preferred_categories = user_prefs.get("categories", ["geral"])
        excluded_topics = user_prefs.get("excluded_topics", [])
        
        all_news = []
        
        # Obter notícias das categorias preferidas
        for category in preferred_categories:
            news = self.fetch_news_by_category(category, limit=10)
            all_news.extend(news)
        
        # Filtrar tópicos excluídos
        if excluded_topics:
            filtered_news = []
            for news_item in all_news:
                exclude = False
                for topic in excluded_topics:
                    if (topic.lower() in news_item["title"].lower() or 
                        topic.lower() in news_item["content"].lower()):
                        exclude = True
                        break
                
                if not exclude:
                    filtered_news.append(news_item)
            
            all_news = filtered_news
        
        # Ordenar por data de publicação (mais recentes primeiro)
        all_news.sort(key=lambda x: x["published_date"], reverse=True)
        
        # Retornar apenas a quantidade solicitada
        return all_news[:count]
    
    def update_user_preference(self, user_id, preferences):
        """Atualiza as preferências de um usuário"""
        str_user_id = str(user_id)  # Garantir que o ID é uma string
        
        if str_user_id not in self.user_preferences:
            self.user_preferences[str_user_id] = {}
            
        # Atualizar categorias se fornecido
        if "categories" in preferences:
            self.user_preferences[str_user_id]["categories"] = preferences["categories"]
            
        # Atualizar tópicos excluídos se fornecido
        if "excluded_topics" in preferences:
            self.user_preferences[str_user_id]["excluded_topics"] = preferences["excluded_topics"]
        
        # Salvar as preferências atualizadas
        try:
            with open(self.user_prefs_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_preferences, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Erro ao salvar preferências do usuário: {e}")
    
    def format_news_for_whatsapp(self, news_items):
        """Formata notícias para enviar pelo WhatsApp"""
        if not news_items:
            return "Não encontramos notícias que correspondam às suas preferências hoje. Tente novamente mais tarde."
        
        intro = random.choice(config.INTRO_MESSAGES)
        formatted_text = f"*{intro}*\n\n"
        
        for i, news in enumerate(news_items, 1):
            title = news["title"]
            summary = news["summary"] if news["summary"] else "Sem resumo disponível."
            url = news["url"]
            
            # Limitar o tamanho do resumo para WhatsApp
            if len(summary) > 150:
                summary = summary[:147] + "..."
            
            formatted_text += f"*{i}. {title}*\n"
            formatted_text += f"{summary}\n"
            formatted_text += f"📰 Leia mais: {url}\n\n"
        
        formatted_text += "💡 *Dica*: Sempre verifique a fonte das notícias que você recebe e desconfie de mensagens alarmistas ou sensacionalistas."
        
        return formatted_text


# Para testes
if __name__ == "__main__":
    fetcher = NewsFetcher()
    # Exemplo de uso
    news = fetcher.fetch_news_by_category("geral", 3)
    print(fetcher.format_news_for_whatsapp(news)) 