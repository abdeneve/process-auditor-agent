import json
import os
import sys
from dotenv import load_dotenv
from typing import TypedDict, List, Dict, Any
from pydantic import BaseModel, Field

from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

class AgentState(TypedDict):
    input_file: str
    data: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    friction_points: str
    report: str

def load_data_node(state: AgentState):
    """Carrega os dados JSON do arquivo de entrada especificado."""
    input_file = state.get("input_file", "input/log_estruturado.json")
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {"data": data}
    except Exception as e:
        return {"data": [], "report": f"Erro ao carregar os dados: {e}"}

def analyze_metrics_node(state: AgentState):
    """Calcula o percentual de cancelamento e extrai os motivos dos cancelamentos."""
    data = state.get("data", [])
    if not data:
        return {"metrics": {"total": 0, "canceled": 0, "cancellation_percentage": 0.0, "reasons": []}}
    
    total = len(data)
    canceled_records = [item for item in data if item.get("status", "").lower() == "cancelada" or item.get("status", "").lower() == "cancelado"]
    canceled_count = len(canceled_records)
    cancellation_percentage = (canceled_count / total) * 100 if total > 0 else 0.0
    
    # Assumindo que a chave 'reason' (motivo) ou similar possa existir caso cancelado, embora não tenhamos visto no trecho
    reasons = {}
    for item in canceled_records:
        reason = item.get("reason", "Motivo não especificado")
        reasons[reason] = reasons.get(reason, 0) + 1
        
    metrics = {
        "total": total,
        "canceled": canceled_count,
        "cancellation_percentage": cancellation_percentage,
        "cancellation_reasons": reasons
    }
    return {"metrics": metrics}

def identify_friction_node(state: AgentState):
    """Usa um LLM para identificar pontos de atrito com base nos dados e métricas."""
    data = state.get("data", [])
    metrics = state.get("metrics", {})
    
    # Pegamos apenas uma amostra se for muito grande, mas para 100 está bom. 
    # Vamos truncar para 50 para o prompt para economizar tokens se quisermos apenas uma amostra, 
    # mas como precisamos encontrar pontos de atrito, podemos enviar um resumo ou os primeiros 50.
    sample_data = data[:50] 
    
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2)
    
    prompt = f"""
    Você é um auditor de processos (Process Auditor) focado no mercado de saúde brasileiro.
    Seu objetivo é identificar pontos de atrito (gargalos, problemas recorrentes) em um processo de agendamento de consultas médicas via WhatsApp ou outros canais em clínicas no Brasil.
    Você também deve responder de forma clara à pergunta: Por que {metrics.get('cancellation_percentage', 0):.2f}% das consultas são canceladas ou não se convertem?
    
    Aqui estão as métricas gerais:
    {json.dumps(metrics, indent=2, ensure_ascii=False)}
    
    Aqui está uma amostra dos dados estruturados coletados das conversas:
    {json.dumps(sample_data, indent=2, ensure_ascii=False)}
    
    Identifique padrões, por exemplo:
    - Falta de informação (ex. convênio médico não fornecido ou null, informações da carteirinha ausentes).
    - Padrões de dias da semana com mais problemas.
    - Respostas ambíguas dos pacientes ou demoras no atendimento.
    
    Responda em português do Brasil (pt-BR), de forma estruturada e profissional.
    """
    
    response = llm.invoke([
        SystemMessage(content="Você é um analista de processos guiado por dados."),
        HumanMessage(content=prompt)
    ])
    
    return {"friction_points": response.content}

def generate_report_node(state: AgentState):
    """Compila o relatório final."""
    metrics = state.get("metrics", {})
    friction_points = state.get("friction_points", "")
    
    report = f"""# Relatório de Auditoria de Processos

## Métricas de Cancelamento
- **Total de Consultas:** {metrics.get('total', 0)}
- **Consultas Canceladas:** {metrics.get('canceled', 0)}
- **Percentual de Cancelamento:** {metrics.get('cancellation_percentage', 0.0):.2f}%

## Motivos de Cancelamento
"""
    reasons = metrics.get("cancellation_reasons", {})
    if not reasons:
        report += "- Não foram registrados cancelamentos ou não foram especificados motivos nos dados fornecidos.\n"
    else:
        for reason, count in reasons.items():
            report += f"- {reason}: {count}\n"
            
    report += f"\n## Pontos de Atrito Identificados\n{friction_points}\n"
    
    return {"report": report}

# Constrói o Grafo
builder = StateGraph(AgentState)
builder.add_node("load_data", load_data_node)
builder.add_node("analyze_metrics", analyze_metrics_node)
builder.add_node("identify_friction", identify_friction_node)
builder.add_node("generate_report", generate_report_node)

builder.add_edge(START, "load_data")
builder.add_edge("load_data", "analyze_metrics")
builder.add_edge("analyze_metrics", "identify_friction")
builder.add_edge("identify_friction", "generate_report")
builder.add_edge("generate_report", END)

graph = builder.compile()

def main():
    load_dotenv()
    
    input_path = "input/log_estruturado.json"
    if len(sys.argv) > 1:
        input_path = sys.argv[1]
        
    initial_state = {"input_file": input_path}
    
    # Define a chave de API padrão se não estiver definida, ou garante que seja carregada do env
    # Nota: O usuário deve ter a GOOGLE_API_KEY definida no ambiente para o langchain_google_genai
    if not os.environ.get("GOOGLE_API_KEY"):
        print("AVISO: A variável de ambiente GOOGLE_API_KEY não está definida. O nó do LLM irá falhar.")
        
    print(f"Executando o Agente Auditor de Processos (Process Auditor) em {input_path}...")
    try:
        result = graph.invoke(initial_state)
        report_content = result.get("report", "Nenhum relatório foi gerado.")
        
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, "relatorio_final.md")
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(report_content)
            
        print("\n" + "="*50 + "\n")
        print(f"Relatório gerado e salvo com sucesso em: {output_file}")
        print("\n" + "="*50 + "\n")
        print(report_content)
        print("\n" + "="*50 + "\n")
    except Exception as e:
        print(f"Falha na execução do grafo: {e}")

if __name__ == "__main__":
    main()
