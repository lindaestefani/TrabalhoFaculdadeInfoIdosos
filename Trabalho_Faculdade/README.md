# InfoIdosos: Sistema de Comunicação Automatizada para Idosos

## Sobre o Projeto

InfoIdosos é um sistema automatizado que visa facilitar o acesso à informação de qualidade para pessoas idosas através do WhatsApp. O projeto busca reduzir a exclusão digital, combater a desinformação e garantir que pessoas de idade avançada tenham acesso a notícias confiáveis sobre temas de seu interesse.

### Objetivos de Desenvolvimento Sustentável Relacionados

- **Redução das desigualdades**: Ao proporcionar acesso facilitado à informação para idosos, contribuímos para a inclusão digital deste grupo social.
- **Consumo e produção responsáveis**: Promovemos o consumo crítico de informações, combatendo fake news e incentivando o uso responsável da tecnologia.

## Funcionalidades

- Envio automatizado de notícias confiáveis via WhatsApp
- Filtro de notícias baseado em preferências do usuário
- Sistema de detecção básica de potenciais fake news
- Análise de interação e feedback para melhorar a personalização
- Interface simplificada pensada para o público idoso

## Como Utilizar

### Requisitos

- Python 3.8 ou superior
- As bibliotecas listadas em `requirements.txt`
- Conta no WhatsApp Business API ou integração com plataforma similar

### Instalação

1. Clone o repositório
2. Instale as dependências com `pip install -r requirements.txt`
3. Configure suas credenciais em um arquivo `.env` (use `.env.example` como modelo)
4. Execute o programa principal com `python app.py`

## Estrutura do Projeto

- `app.py`: Arquivo principal do sistema
- `news_fetcher.py`: Módulo para buscar notícias de fontes confiáveis
- `whatsapp_sender.py`: Módulo para envio de mensagens via WhatsApp
- `fake_news_detector.py`: Módulo com algoritmo simples para detecção de fake news
- `config.py`: Configurações do sistema
- `requirements.txt`: Dependências do projeto

## Contribuindo

Este projeto foi desenvolvido como parte de um trabalho acadêmico sobre "AUTOMATIZAÇÃO DA COMUNICAÇÃO PARA PESSOAS DE IDADE AVANÇADA NA SOCIEDADE MODERNA", mas está aberto a contribuições que visem melhorar a experiência dos usuários idosos. 