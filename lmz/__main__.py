import argparse

import uvicorn
import uvicorn.config

LOGGING_CONFIG = dict(uvicorn.config.LOGGING_CONFIG)
LOGGING_CONFIG["formatters"]["default"] = {
    **LOGGING_CONFIG["formatters"]["default"],
    "fmt": "%(levelprefix)s %(name)s - %(message)s",
}
LOGGING_CONFIG["loggers"]["lmz"] = {
    "handlers": ["default"],
    "level": "DEBUG",
    "propagate": False,
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()

    from .settings import settings

    uvicorn.run(
        "lmz.app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=args.reload,
    )
