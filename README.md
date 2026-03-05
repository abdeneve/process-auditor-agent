# Process Auditor Agent

O **Process Auditor Agent** (Agente Auditor de Processos) é uma ferramenta baseada em IA projetada para analisar logs estruturados de atendimentos (como conversas de WhatsApp de clínicas) e identificar pontos de atrito, métricas de cancelamento e gargalos no processo de agendamento.

Desenvolvido utilizando **LangGraph** para o fluxo de agente e **Gemini 2.5 Flash** (via LangChain) para a análise qualitativa dos dados.

## Funcionalidades

- **Extração de Métricas**: Calcula automaticamente o número total de consultas, a quantidade de cancelamentos e o percentual de conversão/cancelamento.
- **Identificação de Motivos**: Agrupa e contabiliza os principais motivos de cancelamento com base nos dados fornecidos.
- **Análise de Atrito com IA**: Utiliza o poder do modelo Gemini para ler uma amostra dos logs e identificar padrões negativos, falhas na comunicação, demoras no atendimento e outros gargalos.
- **Geração de Relatório**: Compila todas as métricas e a análise da IA em um relatório final detalhado no formato Markdown.

## Pré-requisitos

- Python 3.12 ou superior
- Uma chave de API do Google Gemini (`GOOGLE_API_KEY`)
- [uv](https://github.com/astral-sh/uv) (Recomendado para gerenciamento de dependências)

## Instalação

As dependências deste projeto são gerenciadas via `uv`.

1. Clone o repositório ou acesse a pasta do projeto:
   ```bash
   cd process-auditor-agent
   ```

2. Instale as dependências usando `uv`:
   ```bash
   uv sync
   ```
   *Caso não utilize o uv, você pode instalar as dependências listadas no `pyproject.toml` usando o `pip` padrão.*

## Configuração

Crie um arquivo `.env` na raiz do projeto e adicione sua chave de API do Google:

```env
GOOGLE_API_KEY=sua_chave_api_aqui
```

## Estrutura de Arquivos

- `main.py`: Código principal que contém a definição dos nós do LangGraph e a execução do agente.
- `input/`: Diretório onde o agente busca o arquivo de entrada padrão (`log_estruturado.json`).
- `output/`: Diretório onde o relatório final será gerado.

## Como Usar

Para executar o agente auditor de processos, ative seu ambiente virtual (se aplicável) e execute o script principal:

```bash
# Se usar uv, você pode rodar diretamente com:
uv run main.py
```

Ou usando o Python diretamente:

```bash
python main.py
```

### Arquivo de Entrada Customizado

Por padrão, o agente procurará os dados estruturados em `input/log_estruturado.json`. Você pode passar o caminho para um arquivo diferente via linha de comando:

```bash
python main.py caminho/para/seu/arquivo_customizado.json
```

## Saída

Após a execução, o agente criará a pasta `output/` (caso não exista) e salvará o relatório gerado no arquivo:

```
output/relatorio_final.md
```

Este arquivo conterá as métricas gerais, contagem de motivos de cancelamento e a análise em texto gerada pelo LLM apontando os problemas e possíveis melhorias no processo de atendimento.

## Tecnologias Utilizadas

- [Python](https://www.python.org/)
- [LangChain](https://python.langchain.com/) / [LangChain Google GenAI](https://python.langchain.com/docs/integrations/chat/google_generative_ai/)
- [LangGraph](https://python.langchain.com/docs/langgraph)
- [Pydantic](https://docs.pydantic.dev/)
