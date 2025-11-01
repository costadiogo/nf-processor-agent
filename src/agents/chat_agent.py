"""Chat Assistant para consultas sobre notas fiscais."""

import json
from typing import List

from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain.schema.messages import ToolMessage

from logs.logger import agent_logger
from src.prompts.chat_agent_prompt import SYSTEM_PROMPT

from src.tools.calculate_tool import calcular_totais
from src.tools.find_invoice_by_number_tool import buscar_nota_por_numero
from src.tools.list_invoices_tool import listar_notas_recentes
from src.tools.geral_stats_tool import estatisticas_gerais
from src.tools.get_errors_invoices_tool import buscar_notas_com_erro

# =====================================================
# CHAT ASSISTANT
# =====================================================

class ChatAssistant:
    """Assistente de chat para consultas sobre notas fiscais."""
    
    def __init__(
        self,
        llm_provider: str = "groq",
        api_key: str = ""
    ):
        """Inicializa chat assistant."""
        from config.configuration import DEFAULT_MODELS, LLMProvider
        
        # Buscar modelo padrão do provider
        model = DEFAULT_MODELS[LLMProvider(llm_provider)].value
        
        self.llm = self._setup_llm(llm_provider, api_key, model)
        self.conversation_history: List = [SystemMessage(content=SYSTEM_PROMPT)]
        
        # Registrar ferramentas
        self.tools = [
            buscar_nota_por_numero,
            listar_notas_recentes,
            calcular_totais,
            buscar_notas_com_erro,
            estatisticas_gerais
        ]
        
        # Bind tools ao LLM
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        agent_logger.info(f"💬 Chat Assistant inicializado com {llm_provider}/{model}")
    
    def _setup_llm(self, provider: str, api_key: str, model: str):
        """Configura LLM."""
        provider = provider.lower()
        
        if provider == "openai":
            return ChatOpenAI(api_key=api_key, model=model, temperature=0.1)
        elif provider == "groq":
            return ChatGroq(api_key=api_key, model=model, temperature=0.1)
        elif provider == "claude":
            return ChatAnthropic(api_key=api_key, model=model, temperature=0.1)
        elif provider == "gemini":
            return ChatGoogleGenerativeAI(api_key=api_key, model=model, temperature=0.1)
        else:
            raise ValueError(f"Provider não suportado: {provider}")
    
    def chat(self, user_message: str) -> str:
        """
        Processa mensagem do usuário e retorna resposta.
        
        Args:
            user_message: Mensagem do usuário
        
        Returns:
            Resposta do assistente
        """
        try:
            self.conversation_history.append(HumanMessage(content=user_message))
            
            response = self.llm_with_tools.invoke(self.conversation_history)
            
            self.conversation_history.append(response)
            
            if hasattr(response, 'tool_calls') and response.tool_calls:
                tool_messages = []
                
                for tool_call in response.tool_calls:
                    tool_name = tool_call['name']
                    tool_args = tool_call['args']
                    tool_call_id = tool_call["id"]
                    
                    tool_func = next((t for t in self.tools if t.name == tool_name), None)
                    if tool_func:
                        result = tool_func.invoke(tool_args)
                        tool_results_json = json.dumps(result, ensure_ascii=False)
                        
                        tool_msg = ToolMessage(
                            content=tool_results_json,
                            tool_call_id=tool_call_id
                        )
                        tool_messages.append(tool_msg)
                        agent_logger.info(f"🔧 Ferramenta {tool_name} executada com sucesso.")
                
                self.conversation_history.extend(tool_messages)

                response = self.llm.invoke(self.conversation_history)

            assistant_message = response.content
            self.conversation_history.append(AIMessage(content=assistant_message))
            
            agent_logger.info(f"💬 Resposta gerada com sucesso")
            return assistant_message
            
        except Exception as e:
            agent_logger.error(f"❌ Erro no chat: {e}")
            return f"❌ Desculpe, ocorreu um erro: {str(e)}"
    
    def reset_conversation(self):
        """Reseta o histórico da conversa."""
        self.conversation_history = [SystemMessage(content=SYSTEM_PROMPT)]
        agent_logger.info("🔄 Conversa resetada")
        