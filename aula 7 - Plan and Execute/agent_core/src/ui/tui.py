from rich.console import Console
from rich.live import Live

from utils.loggers import log_panel, log_text
from core.base import AgentBase
from utils.renders import PlanRenderer


renderer = PlanRenderer()


class TuiChat:

    def __init__(self, agent: AgentBase):
        self.agent = agent
        self.console = Console()

    def run(self):
        console = self.console

        log_text("Seu Agente Pessoal está pronto para te ajudar.", level="info", console=console)
        log_text("Digite 'sair' para encerrar\n", level="info", console=console)

        while True:
            user_input = console.input("[bold yellow]Você:[/bold yellow] ")

            if user_input.lower() in ["sair", "exit", "quit"]:
                log_text("Encerrando chat...", level="danger", console=console)
                break

            log_panel(user_input, title="Você", style="user", console=console)

            final_results = None

            with Live(refresh_per_second=6, console=console) as live:
                for event in self.agent.ask(user_input):
                    node_name, state_update = next(iter(event.items()))

                    if "steps" in state_update:
                        renderer.set_steps(state_update["steps"])

                    if "current_step" in state_update:
                        renderer.set_current_step(state_update["current_step"])

                    if "results" in state_update:
                        final_results = state_update["results"]

                    live.update(renderer.render())

            if final_results:
                log_panel(
                    final_results.results_consolidation,
                    title="IA",
                    style="ai",
                    console=console
                )

                if final_results.next_steps:
                    log_panel(
                        final_results.next_steps,
                        title="Próximos passos",
                        style="info",
                        console=console
                    )