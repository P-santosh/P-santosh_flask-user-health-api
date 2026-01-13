pipeline {
    agent any

    environment {
        // --- SonarCloud ---
        SONAR_PROJECT_KEY = "P-santosh_P-santosh_flask-user-health-api"
        SONAR_ORG         = "p-santosh"   // <--- IMPORTANT: replace with your SonarCloud organization key
        SONAR_HOST_URL    = "https://sonarcloud.io"

        // Jenkins Credentials ID where you stored token:
        // Manage Jenkins → Credentials → add "Secret text" → ID = sonar-token
        SONAR_TOKEN = credentials('sonar-token')
    }

    options {
        timestamps()
        ansiColor('xterm')
    }

    stages {

        stage('1. Checkout Source') {
            steps {
                echo "Checking out code from SCM..."
                checkout scm
                sh 'ls -la'
            }
        }

        stage('2. Setup Python venv') {
            steps {
                sh '''
                    set -e
                    echo "Finding Python..."
                    (python3 --version) || (python --version)

                    PYTHON_BIN=$(command -v python3 || command -v python)

                    echo "Python found at: $PYTHON_BIN"
                    $PYTHON_BIN -m venv .venv

                    . .venv/bin/activate
                    python -m pip install --upgrade pip wheel setuptools
                '''
            }
        }

        stage('3. Install Requirements') {
            steps {
                sh '''
                    set -e
                    . .venv/bin/activate

                    if [ -f requirements.txt ]; then
                        pip install -r requirements.txt
                    fi

                    if [ -f requirements-dev.txt ]; then
                        pip install -r requirements-dev.txt
                    else
                        # fallback dev tools
                        pip install pytest pytest-cov flake8 bandit
                    fi
                '''
            }
        }

        stage('4. Build Artefact') {
            steps {
                sh '''
                    set -e
                    echo "Creating build artefact..."

                    mkdir -p artefact
                    tar -czf artefact/flask-user-health-api.tar.gz \
                        app.py requirements.txt Dockerfile tests README.md || true

                    ls -la artefact
                '''
            }
        }

        stage('5. Run Automated Tests') {
            steps {
                sh '''
                    set -e
                    . .venv/bin/activate

                    echo "Running pytest..."
                    pytest -q --disable-warnings --maxfail=1 \
                      --junitxml=test-results.xml \
                      --cov=app --cov-report=xml:coverage.xml --cov-report=term || true
                '''
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: 'test-results.xml'
                    archiveArtifacts artifacts: 'test-results.xml,coverage.xml', allowEmptyArchive: true
                }
            }
        }

        stage('6. Code Quality Analysis (Flake8)') {
            steps {
                sh '''
                    set -e
                    . .venv/bin/activate
                    echo "Running flake8 code quality check..."
                    flake8 . --count --statistics || true
                '''
            }
        }

        stage('7. Security Analysis (Bandit + pip-audit)') {
            steps {
                sh '''
                    set -e
                    . .venv/bin/activate

                    echo "Running Bandit..."
                    bandit -r . -f json -o bandit-report.json || true

                    echo "Running pip-audit..."
                    pip install pip-audit >/dev/null 2>&1 || true
                    pip-audit -f json -o pip-audit-report.json || true
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'bandit-report.json,pip-audit-report.json', allowEmptyArchive: true
                }
            }
        }

        stage('8. Deploy to Test Environment (Docker)') {
            steps {
                sh '''
                    set -e
                    echo "Deploying to staging using Docker Compose..."
                    docker --version
                    docker compose version

                    # Staging deploy
                    docker compose -f docker-compose.staging.yml up -d --build
                    docker compose -f docker-compose.staging.yml ps
                '''
            }
        }

        stage('9. Release to Production (Docker)') {
            steps {
                sh '''
                    set -e
                    echo "Releasing to production..."
                    docker compose -f docker-compose.prod.yml up -d --build
                    docker compose -f docker-compose.prod.yml ps
                '''
            }
        }

        stage('10. Monitoring & Alerting') {
            steps {
                sh '''
                    set -e
                    echo "Monitoring stage..."
                    echo "Checking container health..."
                    docker ps

                    echo "Health check curl (example):"
                    curl -sSf http://localhost:5000/health || true
                '''
            }
        }

        stage('SonarCloud Analysis (Runs after quality)') {
            steps {
                sh '''
                    set -e
                    echo "Running SonarCloud scan..."

                    # Install sonar-scanner locally
                    npm --version || true
                    if ! command -v sonar-scanner >/dev/null 2>&1; then
                        npm install -g sonar-scanner
                    fi

                    sonar-scanner \
                      -Dsonar.projectKey=$SONAR_PROJECT_KEY \
                      -Dsonar.organization=$SONAR_ORG \
                      -Dsonar.host.url=$SONAR_HOST_URL \
                      -Dsonar.token=$SONAR_TOKEN \
                      -Dsonar.python.coverage.reportPaths=coverage.xml
                '''
            }
        }
    }

    post {
        always {
            echo "Archiving artifacts + reports..."
            archiveArtifacts artifacts: 'artefact/*.tar.gz,bandit-report.json,pip-audit-report.json,test-results.xml,coverage.xml', allowEmptyArchive: true
        }
        success {
            echo "✅ SUCCESS: Pipeline completed successfully."
        }
        failure {
            echo "❌ FAILURE: Pipeline failed. Check console output."
        }
    }
}



