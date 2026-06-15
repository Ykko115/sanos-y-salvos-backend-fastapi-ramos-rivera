FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir \
    fastapi==0.110.0 \
    "uvicorn[standard]==0.27.0" \
    "pydantic>=2.9.0" \
    python-dotenv==1.0.1 \
    python-Levenshtein>=0.25.0 \
    "httpx==0.27.0" \
    "requests>=2.31.0" \
    "python-multipart>=0.0.9"

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
