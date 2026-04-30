# Agent Core

## Homework

- Faça um agente inspirado nessa arquitetura (arquitetura do projeto agent_core)

---

## 📐 Breakdown da Arquitetura

### 🎯 Visão Geral

O **Agent Core** é um framework de agente autônomo baseado na arquitetura **Plan & Execute**, que utiliza **LangGraph** para orquestração de estados e **LangChain** para integração com LLMs. O agente segue um fluxo estruturado de 6 fases para executar tarefas complexas.

### 🔄 Fluxo de Execução (Phases)

```
INITIAL → QUERY_REFINING → CONTEXT_GATHERING → CONTEXT_CONSOLIDATION → PLANNING → EXECUTING → WRAPPING_UP → DONE
```

### 📦 Estrutura de Componentes

#### 1. **Core Layer** (`src/core/`)

##### `base.py` - Classe Abstrata do Agente
```python
class AgentBase(ABC):
    @abstractmethod
    def ask(self, query: str)
```
- Define o contrato base para todos os agentes
- Método `ask()` é o ponto de entrada único

##### `graph.py` - Motor de Orquestração
```python
class PlanExecuteAgent(AgentBase)
```
**Responsabilidades:**
- Gerencia o grafo de estados (ExecutionState)
- Orquestra as 6 fases de execução
- Implementa os nós do grafo (assistentes especializados)
- Controla fluxo com base nas phases

**ExecutionState** (Estado do Grafo):
- `phase`: Fase atual da execução
- `query`: Query original do usuário
- `task`: Tarefa refinada (Task)
- `research_plan`: Plano de coleta de contexto (ResearchPlan)
- `context`: Contexto coletado (Context)
- `execution_plan`: Plano de execução (ExecutionPlan)
- `step_counter`: Contador de etapas
- `results`: Resultados finais (RunResults)
- `messages`: Histórico de mensagens

**Métodos Principais:**
- `make_assistant_node()`: Factory para criar nós assistentes especializados
- `make_step_revisor_node()`: Factory para criar revisores de etapas
- `_build_graph()`: Constrói o grafo de execução
- `ask()`: Stream eventos do grafo

##### `prompts.py` - Sistema de Prompts
Define prompts especializados para cada fase:
- `REFINER`: Refina e clarifica a query do usuário
- `CONTEXT_PLANNER`: Planeja coleta de contexto
- `RESEARCH_EXECUTOR`: Executa pesquisa de contexto
- `RESEARCH_CONSOLIDATION`: Consolida informações coletadas
- `PLANNER`: Cria plano de execução
- `PLAN_EXECUTOR`: Executa etapas do plano

#### 2. **Models** (`src/core/models/`)

##### `enums.py` - Estados do Sistema
```python
class Phases(str, Enum):
    INITIAL, QUERY_REFINING, CONTEXT_GATHERING,
    CONTEXT_CONSOLIDATION, PLANNING, EXECUTING,
    WRAPPING_UP, DONE, ERROR
```

##### `outputs.py` - Modelos de Dados
**Estruturas Principais:**

1. **Task** - Tarefa Refinada
   - `description`: Descrição clara da tarefa
   - `intent`: Intenção do usuário

2. **PlanItem** - Item de Plano
   - `quick_description`: Descrição curta
   - `detailed_description`: Descrição detalhada
   - `tools_suggestions`: Ferramentas sugeridas

3. **ResearchPlan** - Plano de Pesquisa
   - `steps`: Lista de PlanItem para coleta de contexto

4. **Context** - Contexto Coletado
   - `items`: Lista de ContextItem (title, content, source)

5. **ExecutionPlan** - Plano de Execução
   - `steps`: Lista de PlanItem para execução

6. **RunResults** - Resultados Finais
   - `used_tools`: Ferramentas utilizadas
   - `detected_problems`: Problemas encontrados
   - `results_consolidation`: Mensagem consolidada
   - `next_steps`: Sugestões de próximos passos

7. **IsStepComplete** - Status de Etapa
   - `isComplete`: Se a etapa foi finalizada
   - `error`: Se houve erro
   - `motif`: Motivo do erro

#### 3. **Tools** (`src/core/tools/`)

##### `fs.py` - Sistema de Arquivos
**Ferramentas Disponíveis:**
- `read_directory()`: Lista arquivos/pastas
- `read_file()`: Lê conteúdo de arquivo
- `write_file()`: Cria/sobrescreve arquivo
- `update_file()`: Adiciona conteúdo ao arquivo
- `move_file()`: Move arquivo
- `delete_file()`: Apaga arquivo
- `create_folder()`: Cria pasta
- `delete_folder()`: Apaga pasta
- `move_folder()`: Move pasta
- `search_files_by_name()`: Busca por padrão
- `search_keyword_in_file()`: Busca palavra-chave
- `read_file_range()`: Lê intervalo de linhas

**Segurança:**
- Todas as operações restritas ao `WORKDIR` (sandbox)
- Validação de paths com `_safe_path()`

#### 4. **UI Layer** (`src/ui/`)

##### `tui.py` - Terminal User Interface
```python
class TuiChat:
    def run(self)
```
- Interface de chat no terminal
- Renderização em tempo real com Rich
- Exibe progresso das etapas
- Mostra resultados consolidados

#### 5. **Utils** (`src/utils/`)

##### Módulos de Suporte:
- `formatters.py`: Formata capabilities das tools
- `loggers.py`: Sistema de logging com Rich
- `mappers.py`: Mapeamento de dados
- `renders.py`: Renderização de planos (PlanRenderer)

### 🏗️ Arquitetura Plan & Execute

#### **Fase 1: QUERY_REFINING**
```
Input: Query do usuário
↓
Prompt: REFINER
↓
Output: Task (description + intent)
```

#### **Fase 2: CONTEXT_GATHERING**
```
Input: Task
↓
Prompt: CONTEXT_PLANNER
↓
Output: ResearchPlan (steps[])
↓
Loop: Para cada step
  ├─ Prompt: RESEARCH_EXECUTOR
  ├─ Tools: context_tools
  ├─ Revisor: IsStepComplete
  └─ Acumula: Context (items[])
```

#### **Fase 3: CONTEXT_CONSOLIDATION**
```
Input: ResearchPlan + Messages
↓
Prompt: RESEARCH_CONSOLIDATION
↓
Output: Context consolidado
```

#### **Fase 4: PLANNING**
```
Input: Context + Task
↓
Prompt: PLANNER
↓
Output: ExecutionPlan (steps[])
```

#### **Fase 5: EXECUTING**
```
Input: ExecutionPlan
↓
Loop: Para cada step
  ├─ Prompt: PLAN_EXECUTOR
  ├─ Tools: execution_tools
  ├─ Revisor: IsStepComplete
  └─ Acumula: Messages
```

#### **Fase 6: WRAPPING_UP**
```
Input: Todas as mensagens da execução
↓
Consolidação
↓
Output: RunResults
  ├─ used_tools[]
  ├─ detected_problems[]
  ├─ results_consolidation
  └─ next_steps
```

### 🔧 Tecnologias Utilizadas

- **LangGraph**: Orquestração de estados e grafos
- **LangChain**: Integração com LLMs e ferramentas
- **LangChain-OpenAI**: Provider de LLM
- **Pydantic**: Validação e schemas de dados
- **Rich**: Interface de terminal
- **FastAPI/Uvicorn**: API REST (futuro)
- **Python 3.13**: Runtime

### 🎨 Padrões de Design

1. **State Machine Pattern**: Gerenciamento de fases via Enum
2. **Factory Pattern**: `make_assistant_node()` e `make_step_revisor_node()`
3. **Strategy Pattern**: Diferentes prompts para diferentes fases
4. **Builder Pattern**: Construção do grafo em `_build_graph()`
5. **Observer Pattern**: Stream de eventos via `graph.stream()`

### 🔑 Características Principais

1. **Separação de Concerns**: Context gathering vs Execution
2. **Ferramentas Segregadas**: context_tools vs execution_tools
3. **Segurança**: Sandbox filesystem (WORKDIR)
4. **Streaming**: Eventos em tempo real
5. **Structured Output**: Pydantic schemas para respostas do LLM
6. **Revisão de Etapas**: Validação automática de conclusão
7. **Consolidação**: Resultados organizados e próximos passos

### 🚀 Fluxo de Inicialização

```python
agent = PlanExecuteAgent(
    model="gpt-4",
    context_tools=[read_file, search_files],
    execution_tools=[write_file, update_file]
)

for event in agent.ask("Crie um projeto Python"):
    # Processa eventos do grafo
    phase = event["phase"]
    # Atualiza UI, etc.
```

### 💡 Conceitos Chave

- **Two-Phase Approach**: Primeiro coleta contexto, depois executa
- **Tool Specialization**: Ferramentas diferentes para research vs execution
- **Iterative Refinement**: Cada fase refina o resultado anterior
- **Self-Correction**: Revisores verificam conclusão de etapas
- **Transparency**: Usuário vê cada etapa sendo executada
