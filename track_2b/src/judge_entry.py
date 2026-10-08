"""Translate the official judge environment into the existing public client."""
import os


def configure(env):
    mode = env.get("APERTUS_MODE", "live").lower()
    if mode not in {"live", "mock"}:
        raise ValueError("APERTUS_MODE must be live or mock")
    env["APERTUS_MODE"] = mode
    if mode == "live":
        for official, existing in (("LLM_NAME", "APERTUS_MODEL"),
                                   ("LLM_BASE_URL", "APERTUS_BASE_URL"),
                                   ("LLM_API_KEY", "APERTUS_API_KEY")):
            if env.get(official):
                env[existing] = env[official]
        if not env.get("APERTUS_MODEL") or not env.get("APERTUS_BASE_URL"):
            raise ValueError("Live mode requires LLM_NAME and LLM_BASE_URL (or APERTUS equivalents)")
        # A self-hosted endpoint may intentionally require no API key.
        # Hosted services still enforce their own authentication.
    env.setdefault("HOST", "0.0.0.0")
    env.setdefault("PORT", "8080")


if __name__ == "__main__":
    configure(os.environ)
    from app.server import main
    main()
