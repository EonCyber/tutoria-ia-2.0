from rich.console import Console
from rich.panel import Panel
from rich.text import Text

_console = Console()

STYLES = {
    "user": "bold yellow",
    "ai": "bold cyan",
    "system": "bold green",
}

def log_panel(content: str, title: str = "", style: str = "ai", console: Console = None):
    """Print a Rich Panel with styled text.

    Args:
        content: The text content to display inside the panel.
        title: The panel title.
        style: One of "user", "ai", or "system" (default: "ai").
        console: Optional Rich Console instance; uses module-level console if omitted.
    """
    resolved_style = STYLES.get(style, STYLES["ai"])
    (console or _console).print(Panel(Text(content, style=resolved_style), title=title))


TEXT_STYLES = {
    "info": "bold cyan",
    "warning": "bold yellow",
    "danger": "bold red",
}


def log_text(content: str, level: str = "info", console: Console = None):
    """Print plain styled text for info, warning, or danger levels."""
    resolved_style = TEXT_STYLES.get(level, TEXT_STYLES["info"])
    (console or _console).print(Text(content, style=resolved_style))
