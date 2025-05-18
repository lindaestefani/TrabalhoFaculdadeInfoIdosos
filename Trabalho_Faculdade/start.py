#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import argparse
import sys
import subprocess

"""
Script de inicialização do InfoIdosos
"""

def check_dependencies():
    """Verifica se todas as dependências estão instaladas"""
    try:
        import dotenv
        import pywhatkit
        import requests
        import bs4
        import newspaper
        import pandas
        import nltk
        import feedparser
        import schedule
        import flask
        import textblob
        import matplotlib
        import sklearn
        print("✅ Todas as dependências estão instaladas.")
        return True
    except ImportError as e:
        print(f"❌ Dependência faltando: {e}")
        print("Por favor, execute 'pip install -r requirements.txt' para instalar todas as dependências.")
        return False

def create_directories():
    """Cria os diretórios necessários"""
    dirs = ['data', 'data/cache', 'templates']
    for directory in dirs:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✅ Diretório criado: {directory}")
    return True

def check_env_file():
    """Verifica se o arquivo .env existe"""
    if not os.path.exists('.env'):
        print("⚠️ Arquivo .env não encontrado.")
        if os.path.exists('.env.example'):
            print("Encontramos o arquivo .env.example. Deseja criar um arquivo .env a partir dele? (s/n)")
            choice = input().lower()
            if choice == 's':
                with open('.env.example', 'r') as example_file:
                    with open('.env', 'w') as env_file:
                        env_file.write(example_file.read())
                print("✅ Arquivo .env criado. Por favor, edite-o com suas credenciais.")
            else:
                print("⚠️ Por favor, crie um arquivo .env com suas configurações antes de continuar.")
        else:
            print("⚠️ Não foi possível encontrar o arquivo .env.example. Por favor, crie um arquivo .env manualmente.")

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description="InfoIdosos - Script de inicialização")
    parser.add_argument('--check', action='store_true', help='Apenas verifica as dependências')
    parser.add_argument('--setup', action='store_true', help='Configura o ambiente')
    parser.add_argument('--add-user', action='store_true', help='Adiciona um novo usuário')
    parser.add_argument('--send-now', action='store_true', help='Envia notícias agora')
    parser.add_argument('--web', action='store_true', help='Inicia apenas a interface web')
    parser.add_argument('--scheduler', action='store_true', help='Inicia apenas o agendador')
    parser.add_argument('--port', type=int, default=5000, help='Porta para a interface web')
    
    args = parser.parse_args()
    
    if args.check:
        check_dependencies()
        return
    
    if args.setup:
        check_dependencies()
        create_directories()
        check_env_file()
        return
    
    if not check_dependencies():
        return
    
    # Preparar comando para app.py
    cmd = [sys.executable, 'app.py']
    
    if args.add_user:
        cmd.append('--add-user')
    elif args.send_now:
        cmd.append('--send-now')
    elif args.web:
        cmd.append('--web')
        cmd.extend(['--port', str(args.port)])
    elif args.scheduler:
        cmd.append('--scheduler')
    else:
        # Modo padrão: iniciar tudo
        cmd.extend(['--port', str(args.port)])
    
    # Executar o comando
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nPrograma encerrado pelo usuário.")
    except Exception as e:
        print(f"Erro ao executar o programa: {e}")

if __name__ == "__main__":
    print("=" * 50)
    print("InfoIdosos - Sistema de Comunicação para Idosos")
    print("=" * 50)
    main() 