"""
CLI entrypoint — run from `backend/` so `app` resolves as a package:

    uvicorn main:app --reload --host 0.0.0.0 --port 8000

Or:

    python main.py
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
