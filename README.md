# Flask User Health API (SIT753 7.3HD DevSecOps Pipeline Project)

This repo is designed to hit **all 7 pipeline stages** required for **SIT753 7.3HD**:
Build → Test → Code Quality → Security → Deploy (Staging) → Monitoring → Release (Prod)

## API Endpoints
- `GET /health` → returns `{"status":"ok"}` (used for monitoring stage)
- `GET /users` → list users
- `POST /users` → create user: `{"name":"...","email":"..."}`
- `GET /users/<id>` → get user
- `DELETE /users/<id>` → delete user

## How to run (local)
```bash
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
# open http://localhost:5000/health
```

## How to run tests
```bash
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q
```

## How to run with Docker (staging + prod)
Build:
```bash
docker build -t flask-user-health-api:local .
```

Staging (port 5050):
```bash
docker tag flask-user-health-api:local flask-user-health-api:staging
docker compose -f docker-compose.staging.yml up -d
curl -s http://localhost:5050/health
```

Prod (port 5060):
```bash
docker tag flask-user-health-api:local flask-user-health-api:prod
docker compose -f docker-compose.prod.yml up -d
curl -s http://localhost:5060/health
```

Stop:
```bash
docker compose -f docker-compose.staging.yml down
docker compose -f docker-compose.prod.yml down
```

## Jenkins setup notes (SonarCloud)
- Jenkins credential:
  - **ID**: `SONAR_TOKEN`
  - **Kind**: Secret text
  - **Secret**: your SonarCloud token
- Jenkins global configuration:
  - SonarQube server name: `SonarCloud`
  - Server URL: `https://sonarcloud.io`
- Jenkins Tools:
  - SonarQube Scanner name: `SonarScanner`

## SonarCloud identifiers used
- `sonar.organization=P-santosh`
- `sonar.projectKey=P-santosh_flask-user-health-api`
