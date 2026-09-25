# API CORS patch

For local browser development, add this to the FastAPI app after creating `app`:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

For deployment, replace the origin with the actual frontend domain rather than using a wildcard.
