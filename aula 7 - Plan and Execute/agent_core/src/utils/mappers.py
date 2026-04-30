from typing import Callable
from core.models.enums import Phases

class InputMapper:
    """
    Classe responsável por mapear os dados de entrada para cada nó do grafo de execução.
    
    Cada nó do grafo necessita de diferentes partes do estado global. O InputMapper
    extrai apenas os dados relevantes para cada nó, mantendo a separação de responsabilidades
    e evitando que os nós recebam informações desnecessárias.
    """

    @staticmethod
    def map(node_name: str) -> Callable:
        """
        Retorna a função de mapeamento apropriada para o nó especificado.
        
        Args:
            node_name: Nome do nó para o qual o mapeamento será aplicado.
                      Valores válidos: 'query_refiner', 'context', 'planner', 'executor', 'results'
        
        Returns:
            Callable: Função lambda que extrai os dados necessários do estado para o nó.
        
        Raises:
            ValueError: Se o node_name não for reconhecido.
            KeyError: Se o estado não contiver as chaves necessárias para o nó.
        """
         
        input_map = {
            # Nó de refinamento: recebe apenas a query original do usuário
            "refiner": lambda state: {
                "query": state["query"],
            },

            # Nó de contexto: recebe a tarefa refinada para coletar contexto
            "context_planner": lambda state: {
                "task": state["task"],
            },
            # Nó de execução: recebe o passo atual e o contexto para executar a ação
            "research_executor": lambda state: {
                "step": state["research_plan"].steps[state["step_counter"]],
                "context": state.get("context").items,
                "messages": state.get("messages", []),
            },
           
            # Nó de consolidação de contexto: recebe o plano de pesquisa e as mensagens para consolidar o contexto
            "context_consolidation": lambda state: {
                "plan": state["research_plan"].model_dump(),
                "messages": state.get("messages", []),
            },
            # Nó de planejamento: recebe a tarefa e o contexto coletado para criar o plano
            "planner": lambda state: {
                "task": state["task"],
                "context": state.get("context").model_dump(),
            },
            # Nó de execução do plano: recebe o passo atual do plano de execução e o contexto para executar a ação
             "plan_executor": lambda state: {
                "step": state["execution_plan"].steps[state["step_counter"]],
                "messages": state.get("messages", []),
            },
            # Nó de resultados: recebe todos os passos executados e o contexto para consolidar
            "wrapping_up": lambda state: {
                "plan": state.get("execution_plan").model_dump(),
                "messages": state.get("messages", []),
            },
        }
         
        # Valida se o nó existe no mapeamento
        if node_name not in input_map:
            raise ValueError(
                f"Nó '{node_name}' não reconhecido. "
                f"Nós válidos: {', '.join(input_map.keys())}"
            )
        
        mapper_func = input_map[node_name]
        # Retorna a função de mapeamento para o nó solicitado
        return mapper_func


class OutputMapper:
    """
    Classe responsável por mapear os dados de saída de cada nó de volta para o estado global.
    
    Cada nó retorna um resultado que precisa ser integrado ao estado. O OutputMapper
    define como cada resultado deve atualizar o estado, mantendo a consistência
    e evitando sobrescritas indevidas.
    """

    @staticmethod
    def map(node_name: str) -> Callable:
        """
        Retorna a função de mapeamento de saída apropriada para o nó especificado.
        
        Args:
            node_name: Nome do nó cujo resultado será mapeado.
        
        Returns:
            Callable: Função que recebe (result, state) e retorna o estado atualizado.
        
        Raises:
            ValueError: Se o node_name não for reconhecido.
        """
        
        output_map = {
            # Nó de refinamento: adiciona a tarefa refinada ao estado
            "refiner": lambda result, state: {
                **state,
                "task": result,
                "phase": Phases.CONTEXT_GATHERING,
            },
            # Nó de contexto: adiciona os itens de contexto coletados ao estado
            "context_planner": lambda result, state: {
                **state,
                "research_plan": result,
                "step_counter": 0,
            },
            "research_executor": lambda result, state: {
                **state,
                "messages": [result],
            },
            "research_consolidation": lambda result, state: {
                **state,
                "context": result,
                "phase": Phases.PLANNING,
            },
            "planner": lambda result, state: {
                **state,
                "execution_plan": result,
                "step_counter": 0,
                "phase": Phases.EXECUTING,
            },
            "plan_executor": lambda result, state: {
                **state,
                "messages": [result],
            },
            "wrapping_up": lambda result, state: {
                **state,
                "results": result, 
                "phase": Phases.DONE,
            },

        }
        
        # Valida se o nó existe no mapeamento
        if node_name not in output_map:
            raise ValueError(
                f"Nó '{node_name}' não reconhecido. "
                f"Nós válidos: {', '.join(output_map.keys())}"
            )
        
        mapper_func = output_map[node_name]
        # Retorna a função de mapeamento de saída para o nó solicitado
        return mapper_func
    

