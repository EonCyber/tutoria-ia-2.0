from pydantic import BaseModel, Field
from typing import List

class Task(BaseModel):
    description: str = Field(
        ...,
        description="Descrição clara e objetiva da tarefa refinada"
    )
    intent: str = Field(
        ...,
        description="Intenção do usuário resumida em uma frase"
    )

class PlanItem(BaseModel):
    quick_description: str = Field(
        ...,
        description="Descrição curta e direta da ação a ser executada"
    )
    detailed_description: str = Field(
        ...,
        description="Descrição detalhada da ação, incluindo como executar e o que se espera obter"
    )
    tools_suggestions: List[str] = Field(
        default_factory=list,
        description="Lista de nomes de ferramentas sugeridas para executar a ação"
    )

class ResearchPlan(BaseModel):
    steps: List[PlanItem] = Field(
        default_factory=list,
        description="Etapas ordenadas de execução para coleta de contexto"
    )   

class ContextItem(BaseModel):
    title: str = Field(
        ...,
        description="Título curto que resume a informação coletada"
    )
    content: str = Field(
        ...,
        description="Conteúdo relevante coletado"
    )
    source: str = Field(
        ...,
        description="Origem da informação (ex: ferramenta ou fonte)"
    )

class Context(BaseModel):
    items: List[ContextItem] = Field(
        default_factory=list,
        description="Lista de contextos coletados"
    )


class ExecutionPlan(BaseModel):
    steps: List[PlanItem] = Field(
        default_factory=list,
        description="Etapas ordenadas para execução da Task"
    )


class UsedTool(BaseModel):
    name: str = Field(
        ...,
        description="Nome da ferramenta utilizada"
    )
    description: str = Field(
        ...,
        description="Descrição do que a ferramenta fez"
    )

class RunResults(BaseModel):
    used_tools: List[UsedTool] = Field(
        default_factory=list,
        description="Lista de ferramentas utilizadas durante a execução"
    )
    detected_problems: List[str] = Field(
        default_factory=list,
        description="Problemas ou limitações encontrados durante a execução"
    )
    results_consolidation: str = Field(
        ...,
        description="Mensagem final consolidada que será entregue ao usuário"
    )
    next_steps: str = Field(
        ...,
        description="Texto sugerindo próximos passos para o usuário"
    )

class IsStepComplete(BaseModel):
    """Indica se um passo foi executado corretamente"""
    isComplete: bool = Field(description="Indica se o passo foi finalizado.")
    error: bool = Field(description="Indica se houve erro na execução do passo.")
    motif: str = Field(description="Motivo do erro, se houver.")