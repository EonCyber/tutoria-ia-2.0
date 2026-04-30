def build_capabilities(tools):
        return "\n".join(
            f"- {t.name}: {t.description}"
            for t in tools
        )
