import argparse

import uvicorn

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
