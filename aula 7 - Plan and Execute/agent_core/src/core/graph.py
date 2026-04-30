

from datetime import datetime

from langchain.chat_models import init_chat_model
from langgraph.graph import MessagesState
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda

from core.base import AgentBase
from core.models.enums import Phases
from core.models.outputs import Context, ExecutionPlan, IsStepComplete, ResearchPlan, Task, RunResults
from utils.formatters import build_capabilities
from typing import Annotated

def replace(_: str, new: str) -> str:
    return new

class ExecutionState(MessagesState):
    phase: Annotated[str, replace] = Phases.INITIAL
    query: Annotated[str, replace] = ""
    task: Annotated[Task, replace]
    research_plan: Annotated[ResearchPlan, replace]
    context: Annotated[Context, replace]
    execution_plan: Annotated[ExecutionPlan, replace]
    step_counter: Annotated[int, replace] = 0
    results: Annotated[RunResults, replace]

class PlanExecuteAgent(AgentBase):
    """
    Agente responsável por planejar e executar ações para atingir um objetivo específico.
    Ele utiliza uma abordagem de planejamento e execução, onde primeiro elabora um plano de ação
    e depois executa as ações planejadas, monitorando os resultados e ajustando o plano conforme necessário.
    """

    def __init__(self, model: str, context_tools: list, execution_tools: list, ):

        self.llm = init_chat_model(model=model, temperature=0.6)
        self.context_tools = context_tools
        self.execution_tools = execution_tools

        if self.context_tools:
            self.context_capabilities = build_capabilities(context_tools)
        if self.execution_tools:
            self.execution_capabilities = build_capabilities(execution_tools)
        
        self.fixed_thread_id = "main_thread"
        
        self.graph = self._build_graph()

    # ---------------------------------
    #               UTIL
    # ---------------------------------
    def save_graph_schema(self, graph):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = f"./plan_execute_graph_{timestamp}.mmd"

        mermaid_code = graph.get_graph(xray=True).draw_mermaid()
        with open(file_path, "w") as f:
            f.write(mermaid_code)
        print(f"Graph Schema Salvo!")
    # ---------------------------------
    #               NODES
    # ---------------------------------
    def make_assistant_node(
            self,
            system_prompt: str,
            dynamic_prompt: str,
            tools = None,
            input_mapper = None,
            llm_output_transformer = lambda state: {"messages": state["messages"]},
            output_mapper = lambda result, _: {"messages": [result]},
    ):
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", dynamic_prompt)
        ])
        inputs = RunnableLambda(input_mapper)

        # LLM FUNNEL
        llm = self.llm
        if tools:
            llm = llm.with_tools(tools)
        if llm_output_transformer:
            llm = llm_output_transformer(llm)
        
        chain = inputs | prompt | llm

        def assistant_node(state: ExecutionState) -> ExecutionState:
            result = chain.invoke(state)

            result_state = output_mapper(result, state)
            return  { **result_state }
        
        return assistant_node

    def make_step_revisor_node(
            self,
            system_prompt: str,
            dynamic_prompt: str,
            input_mapper = None,
            mode: str = "research"
            ):
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", dynamic_prompt)
        ])
        inputs = RunnableLambda(input_mapper)

        chain =  ( inputs | prompt | self.llm.with_structured_output(IsStepComplete))

        def research_revisor_node(state: ExecutionState) -> ExecutionState:
            result = chain.invoke(state)

            # PROXIMO PASSO ou PLANO COMPLETO
            next_counter = state["step_counter"] + 1

            if next_counter >= len(state["research_plan"].steps):
                return {
                    "messages": [ ("ai", "Pesquisa de Contexto Concluída!")],
                    "step_counter": -1,
                    "phase": Phases.CONTEXT_CONSOLIDATION
                }
            elif result.isComplete:
                return {
                    "messages": [("ai", f"Passo concluído, seguindo para o próximo passo...")],
                    "step_counter": next_counter,
                    "phase": Phases.CONTEXT_GATHERING
                }


        def step_revisor_node(state: ExecutionState) -> ExecutionState:
            result = chain.invoke(state)

            # PROXIMO PASSO ou PLANO COMPLETO
            next_counter = state["step_counter"] + 1

            if next_counter >= len(state["research_plan"].steps):
                return {
                    "messages": [ ("ai", "Passos do Plano Concluídos!")],
                    "step_counter": -1,
                    "phase": Phases.WRAPPING_UP
                }
            elif result.isComplete:
                return {
                    "messages": [("ai", f"Passo concluído, seguindo para o próximo passo...")],
                    "step_counter": next_counter,
                    "phase": Phases.EXECUTING
                }

        if mode == "research":
            return research_revisor_node
        return step_revisor_node
    # ---------------------------------
    #          CONDITIONS/ROUTERS
    # ---------------------------------


    def _build_graph(self):
        pass

    def ask(self, query: str):
        initial_state = {
            "messages": [("human", query)],
            "phase": Phases.INITIAL,
            "step_counter": 0
        }

        for event in self.graph.stream(
            initial_state,
            config={"configurable": {"thread_id": self.fixed_thread_id}}
        ):
            yield event

"""
┌──────────────────────────────┐
│      QUERY REFINING          │
├──────────────────────────────┤
│ Input: user_input            │
│ Output: Task                 │
│   - description              │
│   - intent                   │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│     CONTEXT GATHERING        │
├──────────────────────────────┤
│ Output: ResearchPlan         │
│   - steps[]                  │
│ Execução dos steps → Context │
│   - items[]                  │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│          PLANNING            │
├──────────────────────────────┤
│ Input: Context               │
│ Output: ExecutionPlan        │
│   - steps[]                  │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│          EXECUTING           │
├──────────────────────────────┤
│ Execução dos steps           │
│ (tools / ações)              │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│        WRAPPING UP           │
├──────────────────────────────┤
│ Output: RunResults           │
│   - used_tools               │
│   - detected_problems        │
│   - results_consolidation    │
│   - next_steps               │
└──────────────────────────────┘
"""