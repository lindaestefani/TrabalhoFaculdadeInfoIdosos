import requests
from bs4 import BeautifulSoup
import webbrowser
from urllib.parse import quote
import time
from datetime import datetime

def buscar_noticias():
    """Função simples para buscar notícias do G1"""
    try:
        print("Buscando notícias no G1...")
        response = requests.get("https://g1.globo.com/", timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Buscar manchetes
        noticias = []
        # Tentar diferentes seletores usados pelo G1
        elementos = soup.select('.feed-post-body-title')
        if not elementos:
            elementos = soup.select('.feed-post-link')
        if not elementos:
            elementos = soup.select('.bstn-hl-title')
            
        # Limitar a 5 notícias
        for i, elemento in enumerate(elementos[:5]):
            titulo = elemento.get_text().strip()
            # Melhorar a extração do link
            link = elemento.get('href')
            if not link:
                link = elemento.parent.get('href')
            if not link:
                link = elemento.parent.parent.get('href')
                
            noticias.append({
                "numero": i+1,
                "titulo": titulo,
                "link": link
            })
        
        return noticias
    except Exception as e:
        print(f"Erro ao buscar notícias: {e}")
        return []

def formatar_mensagem(noticias):
    """Formata as notícias para envio via WhatsApp"""
    if not noticias:
        return "Não foi possível buscar notícias no momento. Tente novamente mais tarde."
    
    # Escolher saudação com base na hora do dia
    hora_atual = datetime.now().hour
    if hora_atual < 12:
        saudacao = "Bom dia"
    elif hora_atual < 18:
        saudacao = "Boa tarde"
    else:
        saudacao = "Boa noite"
    
    mensagem = f"*InfoIdosos - {saudacao}!*\n\n"
    mensagem += "Aqui estão as principais notícias de hoje:\n\n"
    
    for noticia in noticias:
        mensagem += f"*{noticia['numero']}. {noticia['titulo']}*\n"
        if noticia['link']:
            mensagem += f"📰 Leia mais: {noticia['link']}\n\n"
        else:
            mensagem += "🔍 Link não disponível\n\n"
    
    mensagem += "💡 *Dica*: Sempre verifique a fonte das notícias que você recebe e desconfie de mensagens alarmistas."
    
    return mensagem

def enviar_whatsapp(numero, mensagem):
    """Envia mensagem via WhatsApp Web"""
    # Formatar número de telefone
    numero_formatado = ''.join(filter(str.isdigit, numero))
    if len(numero_formatado) <= 11:
        numero_formatado = "55" + numero_formatado
    
    # Codificar a mensagem para URL
    mensagem_codificada = quote(mensagem)
    
    # Criar URL do WhatsApp
    url = f"https://web.whatsapp.com/send?phone={numero_formatado}&text={mensagem_codificada}"
    
    print(f"\nPreparando para enviar mensagem para +{numero_formatado}")
    print("Abrindo WhatsApp Web...")
    
    # Abrir navegador com WhatsApp Web
    webbrowser.open(url)
    
    print("\nInstruções:")
    print("1. Aguarde o WhatsApp Web carregar completamente.")
    print("2. Quando a página abrir, a mensagem já estará preenchida.")
    print("3. Clique no botão de enviar (seta verde).")
    print("\nAtenção: Mantenha seu celular conectado ao WhatsApp Web.")

def escolher_noticia(noticias):
    """Permite ao usuário escolher uma notícia para ler"""
    while True:
        print("\nEscolha uma notícia para ler (digite o número) ou '0' para voltar:")
        for noticia in noticias:
            print(f"{noticia['numero']}. {noticia['titulo']}")
        
        escolha = input("\nSua escolha: ")
        
        try:
            escolha = int(escolha)
            if escolha == 0:
                return
            if 1 <= escolha <= len(noticias):
                noticia_escolhida = noticias[escolha-1]
                if noticia_escolhida['link']:
                    print(f"\nAbrindo notícia: {noticia_escolhida['titulo']}")
                    webbrowser.open(noticia_escolhida['link'])
                else:
                    print("Desculpe, não foi possível encontrar o link desta notícia.")
            else:
                print("Escolha inválida. Tente novamente.")
        except ValueError:
            print("Por favor, digite um número válido.")

def main():
    print("=" * 50)
    print("InfoIdosos - Sistema Simplificado de Envio de Notícias")
    print("=" * 50)
    print("\nEste programa busca as notícias mais recentes e as envia via WhatsApp.")
    
    # Buscar notícias
    print("\nBuscando notícias atualizadas...")
    noticias = buscar_noticias()
    
    if not noticias:
        print("Erro: Não foi possível encontrar notícias. Verifique sua conexão com a internet.")
        return
    
    print(f"✓ {len(noticias)} notícias encontradas!")
    
    # Mostrar notícias encontradas
    print("\nNotícias disponíveis:")
    for noticia in noticias:
        print(f"{noticia['numero']}. {noticia['titulo']}")
    
    # Perguntar para quem enviar
    print("\n" + "-" * 50)
    numero = input("\nDigite o número de telefone do destinatário (com DDD): ")
    
    # Formatar mensagem
    mensagem = formatar_mensagem(noticias)
    
    # Confirmação
    print("\nMensagem preparada. Pronto para enviar?")
    confirmacao = input("Pressione ENTER para continuar ou digite 'n' para cancelar: ")
    
    if confirmacao.lower() != 'n':
        enviar_whatsapp(numero, mensagem)
        print("\nProcesso iniciado! Siga as instruções no navegador.")
        
        # Oferecer opção de escolher notícia para ler
        print("\nDeseja ler alguma notícia antes de enviar?")
        if input("Digite 's' para sim ou qualquer outra tecla para não: ").lower() == 's':
            escolher_noticia(noticias)
    else:
        print("\nEnvio cancelado pelo usuário.")

if __name__ == "__main__":
    main() 