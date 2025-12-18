# SHL Assessment Recommendation System - Deployment Guide

## Prerequisites

- Python 3.11+
- 4GB RAM minimum
- Windows/Linux/macOS
- Internet connection (first run only for model download)

## Installation

### 1. Clone Repository

```bash
git clone <repository-url>
cd SHL-TASK
```

### 2. Create Virtual Environment

**Windows:**
```powershell
python -m venv .venv311
.venv311\Scripts\Activate.ps1
```

**Linux/macOS:**
```bash
python3 -m venv .venv311
source .venv311/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**Dependencies installed:**
- fastapi==0.104.1
- uvicorn[standard]==0.24.0
- pydantic==2.5.0
- sentence-transformers==2.2.2
- faiss-cpu==1.7.4
- pandas==2.1.3
- openpyxl==3.1.5
- numpy==1.24.3

### 4. Verify Data Files

Ensure these files exist:
- `Gen_AI Dataset.xlsx` (Train-Set and Test-Set sheets)
- `data/shl_catalog.csv` (54 assessments)

## Quick Start

### Option 1: One-Command Execution

```bash
python run.py
```

This will:
1. Build FAISS index
2. Evaluate on train set
3. Generate test predictions
4. Start API server on http://localhost:8000

### Option 2: Step-by-Step

```bash
# Build FAISS index
python vector_store.py

# Evaluate system
python production_evaluator.py

# Generate predictions
python production_csv_generator.py

# Start API
python api_server.py
```

## API Server Deployment

### Local Development

```bash
python api_server.py
```

Server runs at: http://localhost:8000
API docs: http://localhost:8000/docs

### Production with Uvicorn

```bash
uvicorn api_server:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker Deployment

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Download model on build
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Build FAISS index
RUN python vector_store.py

EXPOSE 8000

CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Build and run:**
```bash
docker build -t shl-recommendation-api .
docker run -p 8000:8000 shl-recommendation-api
```

### Docker Compose

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - API_HOST=0.0.0.0
      - API_PORT=8000
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

Run:
```bash
docker-compose up -d
```

## Cloud Deployment

### AWS EC2

1. Launch EC2 instance (t3.medium or larger)
2. SSH into instance
3. Install Python 3.11
4. Clone repository
5. Install dependencies
6. Run with systemd:

**shl-api.service:**
```ini
[Unit]
Description=SHL Recommendation API
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/SHL-TASK
Environment="PATH=/home/ubuntu/SHL-TASK/.venv311/bin"
ExecStart=/home/ubuntu/SHL-TASK/.venv311/bin/uvicorn api_server:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable shl-api
sudo systemctl start shl-api
```

### Azure Web App

```bash
az webapp up --name shl-recommendation-api --resource-group myResourceGroup --runtime "PYTHON:3.11"
```

### Google Cloud Run

```bash
gcloud run deploy shl-recommendation-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## Environment Configuration

**Optional: .env file**
```env
API_HOST=0.0.0.0
API_PORT=8000
EMBEDDING_MODEL=all-MiniLM-L6-v2
TOP_N_RETRIEVAL=20
FINAL_RECOMMENDATIONS=10
```

Load in config.py:
```python
from dotenv import load_dotenv
load_dotenv()
```

## Performance Optimization

### 1. Pre-build FAISS Index

```bash
# Build index once during deployment
python vector_store.py
```

Index files created:
- `data/faiss_index.bin` (54 vectors × 384 dims)
- `data/faiss_metadata.pkl` (assessment metadata)

### 2. Model Caching

First run downloads model (~90MB). Subsequent runs use cached model from:
- Linux: `~/.cache/torch/sentence_transformers/`
- Windows: `C:\Users\<user>\.cache\torch\sentence_transformers\`

### 3. Uvicorn Workers

For production, use multiple workers:
```bash
uvicorn api_server:app --workers 4 --host 0.0.0.0 --port 8000
```

## Monitoring

### Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{"status": "healthy", "message": "System operational"}
```

### Logs

Production logging:
```bash
uvicorn api_server:app --log-level info --access-log
```

## Troubleshooting

### Issue: Module not found

```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Issue: FAISS index not found

```bash
# Rebuild index
python vector_store.py
```

### Issue: Port already in use

```bash
# Change port in config.py or use environment variable
API_PORT=8001 python api_server.py
```

### Issue: Out of memory

Minimum requirements:
- 4GB RAM for model loading
- 1GB disk for model cache
- Use t3.medium or larger on AWS

## Security

### 1. HTTPS/TLS

Use reverse proxy (nginx/caddy):

**nginx.conf:**
```nginx
server {
    listen 443 ssl;
    server_name api.example.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 2. Rate Limiting

Add to api_server.py:
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/recommend")
@limiter.limit("10/minute")
async def recommend(request: Request, req: RecommendationRequest):
    ...
```

### 3. API Key Authentication

```python
from fastapi.security import APIKeyHeader

API_KEY_HEADER = APIKeyHeader(name="X-API-Key")

@app.post("/recommend")
async def recommend(api_key: str = Depends(API_KEY_HEADER)):
    if api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=401)
    ...
```

## Backup

Critical files to backup:
- `data/faiss_index.bin`
- `data/faiss_metadata.pkl`
- `data/shl_catalog.csv`
- `Gen_AI Dataset.xlsx`

## Scaling

### Horizontal Scaling

Deploy multiple instances behind load balancer:

```bash
# Instance 1
uvicorn api_server:app --host 0.0.0.0 --port 8000

# Instance 2
uvicorn api_server:app --host 0.0.0.0 --port 8001

# Load balancer (nginx)
upstream shl_api {
    server localhost:8000;
    server localhost:8001;
}
```

### Kubernetes

**deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: shl-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: shl-api
  template:
    metadata:
      labels:
        app: shl-api
    spec:
      containers:
      - name: api
        image: shl-recommendation-api:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "2Gi"
            cpu: "500m"
```

## Maintenance

### Update Catalog

```bash
# Rebuild catalog from new training data
python -c "from data_processor import DataProcessor; dp = DataProcessor(); catalog = dp.load_catalog()"

# Rebuild FAISS index
python vector_store.py
```

### Update Model

Change in config.py:
```python
EMBEDDING_MODEL = 'all-mpnet-base-v2'  # Larger model
```

Rebuild:
```bash
python vector_store.py
```

## Support

For issues:
1. Check logs: `uvicorn api_server:app --log-level debug`
2. Verify FAISS index: `ls -lh data/faiss_index.bin`
3. Test health endpoint: `curl http://localhost:8000/health`
4. Review evaluation metrics: `cat data/evaluation_results.json`

## License

Internal use only - SHL Assessment Recommendation System
