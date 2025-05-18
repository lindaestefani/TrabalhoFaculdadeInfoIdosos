import time
import logging
import os
import json
from datetime import datetime
import pywhatkit
from twilio.rest import Client
import config

# Configurar logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("whatsapp_sender")

class WhatsAppSender:
    def __init__(self):
        self.log_file = os.path.join(config.DATA_DIR, "message_logs.json")
        self.message_logs = self._load_logs()
        self.use_twilio = config.TWILIO_ACCOUNT_SID and config.TWILIO_AUTH_TOKEN
        
        if self.use_twilio:
            try:
                self.twilio_client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)
                logger.info("Twilio inicializado com sucesso.")
            except Exception as e:
                logger.error(f"Erro ao inicializar Twilio: {e}")
                self.use_twilio = False
    
    def _load_logs(self):
        """Carrega o histórico de mensagens enviadas"""
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Erro ao carregar logs de mensagens: {e}")
                return {}
        return {}
    
    def _save_logs(self):
        """Salva o histórico de mensagens enviadas"""
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(self.message_logs, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Erro ao salvar logs de mensagens: {e}")
    
    def _log_message(self, recipient, message_type, content_summary, success=True, error=""):
        """Registra mensagem enviada no histórico"""
        timestamp = datetime.now().isoformat()
        
        if recipient not in self.message_logs:
            self.message_logs[recipient] = []
        
        log_entry = {
            "timestamp": timestamp,
            "type": message_type,
            "content_summary": content_summary[:100] + "..." if len(content_summary) > 100 else content_summary,
            "success": success,
            "error": error
        }
        
        self.message_logs[recipient].append(log_entry)
        self._save_logs()

    def _format_phone_number(self, phone_number):
        """Formata o número de telefone para o formato correto do WhatsApp"""
        # Remover caracteres não numéricos
        phone = ''.join(filter(str.isdigit, phone_number))
        
        # Adicionar código do país se não tiver
        if len(phone) <= 11:  # Assumindo número brasileiro sem código do país
            phone = "55" + phone
            
        return phone
    
    def send_with_pywhatkit(self, phone_number, message):
        """Envia mensagem usando pywhatkit (método alternativo)"""
        try:
            # Formatar o número de telefone
            formatted_phone = self._format_phone_number(phone_number)
            
            # Obter hora e minuto atual (para envio imediato)
            now = datetime.now()
            current_hour = now.hour
            current_minute = now.minute + 1  # Adicionar 1 minuto para garantir tempo suficiente
            
            # Ajustar para o próximo dia se necessário
            if current_minute >= 60:
                current_minute = 0
                current_hour += 1
            
            if current_hour >= 24:
                current_hour = 0
            
            # Enviar a mensagem
            pywhatkit.sendwhatmsg(
                phone_no=f"+{formatted_phone}", 
                message=message,
                time_hour=current_hour,
                time_min=current_minute,
                wait_time=20,  # Tempo de espera para enviar após abrir o WhatsApp Web
                tab_close=True  # Fechar a aba após o envio
            )
            
            # Aguardar um pouco para garantir que a mensagem seja enviada
            time.sleep(5)
            
            logger.info(f"Mensagem enviada com sucesso via pywhatkit para: {phone_number}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem via pywhatkit: {e}")
            return False
    
    def send_with_twilio(self, phone_number, message):
        """Envia mensagem usando Twilio WhatsApp API"""
        if not self.use_twilio:
            logger.error("Twilio não configurado. Verifique suas credenciais.")
            return False
        
        try:
            # Formatar o número de telefone
            formatted_phone = self._format_phone_number(phone_number)
            
            # Enviar mensagem via Twilio WhatsApp
            message = self.twilio_client.messages.create(
                from_=f'whatsapp:{config.TWILIO_PHONE_NUMBER}',
                body=message,
                to=f'whatsapp:+{formatted_phone}'
            )
            
            logger.info(f"Mensagem enviada com sucesso via Twilio para: {phone_number} (SID: {message.sid})")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem via Twilio: {e}")
            return False
    
    def send_message(self, phone_number, message):
        """Função principal para enviar mensagem via WhatsApp"""
        logger.info(f"Tentando enviar mensagem para: {phone_number}")
        
        # Tentar primeiro com Twilio se configurado
        if self.use_twilio:
            success = self.send_with_twilio(phone_number, message)
            if success:
                self._log_message(phone_number, "whatsapp", message, success=True)
                return True
            else:
                logger.warning("Falha ao enviar via Twilio, tentando método alternativo...")
        
        # Tentar com pywhatkit como alternativa
        success = self.send_with_pywhatkit(phone_number, message)
        
        # Registrar o resultado no log
        if success:
            self._log_message(phone_number, "whatsapp", message, success=True)
        else:
            error_msg = "Não foi possível enviar mensagem por nenhum método."
            self._log_message(phone_number, "whatsapp", message, success=False, error=error_msg)
            logger.error(error_msg)
        
        return success
    
    def get_message_history(self, phone_number):
        """Obtém o histórico de mensagens enviadas para um número"""
        return self.message_logs.get(phone_number, [])

# Para testes
if __name__ == "__main__":
    # Exemplo de uso da classe
    sender = WhatsAppSender()
    
    # Substituir por um número real para testes
    test_phone = "5551999999999"  # Exemplo: +55 (51) 99999-9999
    test_message = """*Teste do InfoIdosos*
    
Este é um teste do sistema de envio de notícias para pessoas idosas.
    
⚠️ *Importante*: Esta é apenas uma mensagem de teste.
    
Responda SIM para confirmar que recebeu esta mensagem."""
    
    print(f"Enviando mensagem de teste para {test_phone}...")
    success = sender.send_message(test_phone, test_message)
    
    if success:
        print("Mensagem enviada com sucesso!")
    else:
        print("Falha ao enviar mensagem. Verifique os logs para mais detalhes.") 