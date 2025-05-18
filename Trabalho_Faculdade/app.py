import os
import sys
import json
import logging
import time
import schedule
import random
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
from flask import Flask, request, jsonify, render_template
import nltk

# Importar nossos módulos
from news_fetcher import NewsFetcher
from whatsapp_sender import WhatsAppSender
from fake_news_detector import FakeNewsDetector
import config

# Configurar logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(config.DATA_DIR, "app.log")),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("app")

# Garantir que os diretórios necessários existam
os.makedirs(config.DATA_DIR, exist_ok=True)
os.makedirs(config.CACHE_DIR, exist_ok=True)

# Inicializar o aplicativo Flask para interface web
app = Flask(__name__)
app.secret_key = os.urandom(24)

# Inicializar os objetos principais
news_fetcher = NewsFetcher()
whatsapp_sender = WhatsAppSender()
fake_news_detector = FakeNewsDetector()

# Arquivo com dados dos usuários
users_file = os.path.join(config.DATA_DIR, "users.json")

def load_users():
    """Carrega lista de usuários do arquivo"""
    if os.path.exists(users_file):
        try:
            with open(users_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Erro ao carregar usuários: {e}")
            return {}
    return {}

def save_users(users):
    """Salva lista de usuários no arquivo"""
    try:
        with open(users_file, 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Erro ao salvar usuários: {e}")

# Carregar lista de usuários
users = load_users()

# ----- Funções Principais para Envio de Notícias -----

def send_daily_news():
    """Função principal que envia notícias diárias para todos os usuários"""
    logger.info("Iniciando envio de notícias diárias...")
    
    if not users:
        logger.warning("Nenhum usuário cadastrado para receber notícias")
        return
    
    for user_id, user_data in users.items():
        if not user_data.get("active", True):
            logger.info(f"Usuário {user_id} está inativo, pulando...")
            continue
        
        try:
            # Obter preferências do usuário
            user_phone = user_data.get("phone")
            if not user_phone:
                logger.warning(f"Usuário {user_id} não tem telefone cadastrado")
                continue
            
            # Verificar frequência de envio do usuário
            send_frequency = user_data.get("frequency", "daily")
            current_day = datetime.now().strftime("%A").lower()
            
            # Pular usuário se a frequência não corresponder ao dia atual
            if send_frequency == "weekly" and current_day != "monday":
                continue
            elif send_frequency == "biweekly" and current_day not in ["monday", "thursday"]:
                continue
            
            # Obter notícias para este usuário
            logger.info(f"Buscando notícias para usuário {user_id}")
            news_count = user_data.get("news_count", config.MAX_NEWS_PER_DAY)
            user_news = news_fetcher.get_news_for_user(user_id, count=news_count)
            
            if not user_news:
                logger.warning(f"Nenhuma notícia encontrada para o usuário {user_id}")
                continue
            
            # Formatar mensagem para WhatsApp
            message = news_fetcher.format_news_for_whatsapp(user_news)
            
            # Enviar mensagem
            logger.info(f"Enviando {len(user_news)} notícias para {user_phone}")
            success = whatsapp_sender.send_message(user_phone, message)
            
            if success:
                # Atualizar estatísticas do usuário
                if "stats" not in user_data:
                    user_data["stats"] = {}
                
                if "messages_sent" not in user_data["stats"]:
                    user_data["stats"]["messages_sent"] = 0
                    
                if "news_sent" not in user_data["stats"]:
                    user_data["stats"]["news_sent"] = 0
                
                user_data["stats"]["messages_sent"] += 1
                user_data["stats"]["news_sent"] += len(user_news)
                user_data["stats"]["last_sent"] = datetime.now().isoformat()
                
                # Salvar usuários atualizados
                save_users(users)
                
            else:
                logger.error(f"Falha ao enviar notícias para o usuário {user_id}")
        
        except Exception as e:
            logger.error(f"Erro ao processar usuário {user_id}: {e}")
    
    logger.info("Envio de notícias diárias concluído")

def send_news_to_user(user_id, count=None):
    """Envia notícias para um usuário específico sob demanda"""
    if user_id not in users:
        logger.warning(f"Usuário {user_id} não encontrado")
        return False
    
    user_data = users[user_id]
    user_phone = user_data.get("phone")
    
    if not user_phone:
        logger.warning(f"Usuário {user_id} não tem telefone cadastrado")
        return False
    
    # Usar contagem específica se fornecida, senão usar preferência do usuário
    if count is None:
        count = user_data.get("news_count", config.MAX_NEWS_PER_DAY)
    
    try:
        # Buscar notícias
        user_news = news_fetcher.get_news_for_user(user_id, count=count)
        
        if not user_news:
            logger.warning(f"Nenhuma notícia encontrada para o usuário {user_id}")
            return False
        
        # Formatar e enviar
        message = news_fetcher.format_news_for_whatsapp(user_news)
        success = whatsapp_sender.send_message(user_phone, message)
        
        if success:
            # Atualizar estatísticas
            if "stats" not in user_data:
                user_data["stats"] = {}
            
            if "messages_sent" not in user_data["stats"]:
                user_data["stats"]["messages_sent"] = 0
                
            if "news_sent" not in user_data["stats"]:
                user_data["stats"]["news_sent"] = 0
            
            user_data["stats"]["messages_sent"] += 1
            user_data["stats"]["news_sent"] += len(user_news)
            user_data["stats"]["last_sent"] = datetime.now().isoformat()
            
            # Salvar usuários atualizados
            save_users(users)
            
            return True
        else:
            return False
        
    except Exception as e:
        logger.error(f"Erro ao enviar notícias para o usuário {user_id}: {e}")
        return False

def add_user(name, phone, categories=None, excluded_topics=None, frequency="daily", news_count=5):
    """Adiciona um novo usuário ao sistema"""
    # Gerar ID único para o usuário
    user_id = str(int(time.time()))
    
    # Verificar se categorias são válidas
    if categories is None:
        categories = ["geral"]
    else:
        valid_categories = []
        for category in categories:
            if category in config.NEWS_SOURCES:
                valid_categories.append(category)
            else:
                logger.warning(f"Categoria inválida ignorada: {category}")
        
        if not valid_categories:
            valid_categories = ["geral"]
        
        categories = valid_categories
    
    # Criar dados do usuário
    user_data = {
        "id": user_id,
        "name": name,
        "phone": phone,
        "active": True,
        "created_at": datetime.now().isoformat(),
        "frequency": frequency,
        "news_count": news_count,
        "stats": {
            "messages_sent": 0,
            "news_sent": 0
        }
    }
    
    # Adicionar usuário à lista
    users[user_id] = user_data
    save_users(users)
    
    # Configurar preferências
    preferences = {
        "categories": categories
    }
    
    if excluded_topics:
        preferences["excluded_topics"] = excluded_topics
    
    news_fetcher.update_user_preference(user_id, preferences)
    
    # Enviar mensagem de boas-vindas
    welcome_message = f"""*Bem-vindo(a) ao InfoIdosos!* 👋

Olá, {name}! Você foi cadastrado(a) com sucesso em nosso serviço de envio de notícias.

Você receberá {news_count} notícias {frequency}, sobre os seguintes temas:
{', '.join(categories)}

Para alterar suas preferências ou caso precise de ajuda, entre em contato com nosso administrador.

*Dica*: Sempre verifique a fonte das notícias que você recebe e desconfie de mensagens alarmistas ou sensacionalistas."""

    whatsapp_sender.send_message(phone, welcome_message)
    
    return user_id

# ----- Rotas da API Flask -----

@app.route('/')
def home():
    """Página inicial da aplicação web"""
    return render_template('index.html', title="InfoIdosos - Sistema de Comunicação para Idosos")

@app.route('/api/users', methods=['GET'])
def get_users():
    """Retorna lista de usuários cadastrados"""
    return jsonify(users)

@app.route('/api/users', methods=['POST'])
def create_user():
    """Cria um novo usuário"""
    data = request.json
    
    if not data or not 'name' in data or not 'phone' in data:
        return jsonify({'error': 'Dados incompletos'}), 400
    
    name = data.get('name')
    phone = data.get('phone')
    categories = data.get('categories')
    excluded_topics = data.get('excluded_topics')
    frequency = data.get('frequency', 'daily')
    news_count = data.get('news_count', 5)
    
    user_id = add_user(name, phone, categories, excluded_topics, frequency, news_count)
    
    return jsonify({'message': 'Usuário criado com sucesso', 'user_id': user_id}), 201

@app.route('/api/users/<user_id>', methods=['PUT'])
def update_user(user_id):
    """Atualiza dados de um usuário"""
    if user_id not in users:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    data = request.json
    if not data:
        return jsonify({'error': 'Dados não fornecidos'}), 400
    
    user_data = users[user_id]
    
    # Atualizar campos básicos
    for field in ['name', 'phone', 'active', 'frequency', 'news_count']:
        if field in data:
            user_data[field] = data[field]
    
    # Atualizar preferências se necessário
    preferences = {}
    
    if 'categories' in data:
        # Verificar se as categorias são válidas
        valid_categories = []
        for category in data['categories']:
            if category in config.NEWS_SOURCES:
                valid_categories.append(category)
        
        if valid_categories:
            preferences['categories'] = valid_categories
    
    if 'excluded_topics' in data:
        preferences['excluded_topics'] = data['excluded_topics']
    
    if preferences:
        news_fetcher.update_user_preference(user_id, preferences)
    
    # Salvar alterações
    save_users(users)
    
    return jsonify({'message': 'Usuário atualizado com sucesso'})

@app.route('/api/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Remove um usuário do sistema"""
    if user_id not in users:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    # Obter informações do usuário antes de remover
    user_data = users[user_id]
    phone = user_data.get('phone')
    name = user_data.get('name')
    
    # Remover usuário
    del users[user_id]
    save_users(users)
    
    # Enviar mensagem de despedida
    if phone:
        goodbye_message = f"""*Até logo do InfoIdosos* 👋

Olá, {name}. Seu cadastro foi removido do nosso sistema de envio de notícias.

Agradecemos por ter utilizado nosso serviço. Se quiser voltar a receber notícias, entre em contato com nosso administrador.

Lembre-se sempre de verificar a fonte das notícias que você recebe!"""
        
        whatsapp_sender.send_message(phone, goodbye_message)
    
    return jsonify({'message': 'Usuário removido com sucesso'})

@app.route('/api/users/<user_id>/send', methods=['POST'])
def send_user_news(user_id):
    """Envia notícias para um usuário específico"""
    if user_id not in users:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    count = request.json.get('count') if request.json else None
    
    success = send_news_to_user(user_id, count)
    
    if success:
        return jsonify({'message': 'Notícias enviadas com sucesso'})
    else:
        return jsonify({'error': 'Falha ao enviar notícias'}), 500

@app.route('/api/broadcast', methods=['POST'])
def broadcast_message():
    """Envia uma mensagem personalizada para todos os usuários ativos"""
    data = request.json
    
    if not data or not 'message' in data:
        return jsonify({'error': 'Mensagem não fornecida'}), 400
    
    message = data['message']
    success_count = 0
    failure_count = 0
    
    for user_id, user_data in users.items():
        if not user_data.get('active', True):
            continue
        
        phone = user_data.get('phone')
        if not phone:
            continue
        
        # Personalizar mensagem com nome do usuário
        personalized_message = message.replace("{nome}", user_data.get('name', ''))
        
        # Enviar mensagem
        success = whatsapp_sender.send_message(phone, personalized_message)
        
        if success:
            success_count += 1
        else:
            failure_count += 1
    
    return jsonify({
        'message': f'Broadcast enviado para {success_count} usuários com sucesso ({failure_count} falhas)'
    })

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Obtém estatísticas gerais do sistema"""
    total_users = len(users)
    active_users = sum(1 for u in users.values() if u.get('active', True))
    
    # Calcular estatísticas de envio
    total_messages = 0
    total_news = 0
    
    for user_data in users.values():
        stats = user_data.get('stats', {})
        total_messages += stats.get('messages_sent', 0)
        total_news += stats.get('news_sent', 0)
    
    # Obter categorias mais populares
    categories_count = {}
    
    for user_id in users.keys():
        user_prefs = news_fetcher.user_preferences.get(user_id, {})
        for category in user_prefs.get('categories', ['geral']):
            categories_count[category] = categories_count.get(category, 0) + 1
    
    top_categories = sorted(categories_count.items(), key=lambda x: x[1], reverse=True)
    
    return jsonify({
        'total_users': total_users,
        'active_users': active_users,
        'total_messages_sent': total_messages,
        'total_news_sent': total_news,
        'top_categories': dict(top_categories[:5]),
        'system_start': os.path.getmtime(os.path.abspath(__file__))
    })

# ----- Configuração do Agendador -----

def setup_scheduler():
    """Configura o agendador para executar tarefas periódicas"""
    # Enviar notícias diárias às 8:00
    schedule.every().day.at(config.DEFAULT_SEND_TIME).do(send_daily_news)
    
    # Log diário às 00:01
    schedule.every().day.at("00:01").do(lambda: logger.info("Relatório diário: Sistema funcionando normalmente"))
    
    logger.info(f"Agendador configurado. Próximo envio de notícias às {config.DEFAULT_SEND_TIME}")

def run_scheduler():
    """Executa o agendador em um loop infinito"""
    setup_scheduler()
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Verificar a cada minuto

# ----- Inicialização do Aplicativo -----

if __name__ == "__main__":
    # Configurar argumentos da linha de comando
    import argparse
    
    parser = argparse.ArgumentParser(description="InfoIdosos - Sistema de comunicação automatizada para idosos")
    parser.add_argument('--web', action='store_true', help='Iniciar a interface web')
    parser.add_argument('--scheduler', action='store_true', help='Iniciar o agendador de tarefas')
    parser.add_argument('--port', type=int, default=5000, help='Porta para a interface web')
    parser.add_argument('--add-user', action='store_true', help='Adicionar novo usuário')
    parser.add_argument('--send-now', action='store_true', help='Enviar notícias agora para todos os usuários')
    
    args = parser.parse_args()
    
    # Ação baseada nos argumentos
    if args.add_user:
        # Interface simples para adicionar usuário
        print("=== Adicionar Novo Usuário ===")
        name = input("Nome: ")
        phone = input("Telefone (com DDD): ")
        categories_input = input("Categorias (separadas por vírgula - geral,saude,tecnologia,economia): ")
        categories = [c.strip() for c in categories_input.split(',')] if categories_input else None
        frequency = input("Frequência (daily/weekly/biweekly) [daily]: ") or "daily"
        
        user_id = add_user(name, phone, categories, None, frequency)
        print(f"Usuário adicionado com ID: {user_id}")
    
    elif args.send_now:
        # Enviar notícias imediatamente para todos os usuários
        print("Enviando notícias para todos os usuários...")
        send_daily_news()
        print("Concluído!")
    
    elif args.scheduler:
        # Iniciar apenas o agendador
        print("Iniciando agendador de tarefas...")
        run_scheduler()
    
    elif args.web:
        # Iniciar apenas a interface web
        print(f"Iniciando interface web na porta {args.port}...")
        app.run(host='0.0.0.0', port=args.port, debug=config.DEBUG_MODE)
    
    else:
        # Comportamento padrão: iniciar web e agendador em threads separados
        import threading
        
        # Thread para o agendador
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        
        # Iniciar a interface web
        print(f"Iniciando sistema completo (web + agendador) na porta {args.port}...")
        app.run(host='0.0.0.0', port=args.port, debug=config.DEBUG_MODE) 