pipeline {
    agent any

    environment {
        VENV_DIR = ".venv"
        APP_NAME = "flask-user-health-api"

        // Docker image name (local)
        DOCKER_IMAGE = "sit753/flask-user-health-api:${BUILD_NUMBER}"

        // SonarCloud
        SONAR_PROJECT_KEY = "P-santosh_P-santosh_flask-user-health-api"
        SONAR_ORG = "p-santosh"
        SONAR_HOST_URL = "https://sonarcloud.io"

        // Sonar Scanner version
        SONAR_SCANNER_VERSION = "5.0.1.3006"
        SONAR_SCANNER_DIR = ".sonar/sonar-scanner"
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
                sh "ls -la"
            }
        }

        stage('2. Setup Python venv') {
            steps {
                sh '''
                    set -e

                    echo "Detecting python..."
                    if command -v python3.11 >/dev/null 2>&1; then
                        PY=python3.11
                    elif command -v python3.10 >/dev/null 2>&1; then
                        PY=python3.10
                    elif command -v python3 >/dev/null 2>&1; then
                        PY=python3
                    elif command -v python >/dev/null 2>&1; then
                        PY=python
                    else
                        echo "❌ ERROR: Python not found on Jenkins agent."
                        exit 1
                    fi

                    echo "Using Python: $PY"
                    $PY --version

                    echo "Creating venv..."
                    $PY -m venv ${VENV_DIR}

                    echo "Activating venv..."
                    . ${VENV_DIR}/bin/activate

                    python --version
                    pip --version
                    pip install --upgrade pip
                '''
            }
        }

        stage('3. Install Requirements') {
            steps {
                sh '''
                    set -e
                    . ${VENV_DIR}/bin/activate

                    echo "Installing requirements..."
                    pip install -r requirements.txt
                    if [ -f requirements-dev.txt ]; then
                        pip install -r requirements-dev.txt
                    fi
                '''
            }
        }

        stage('4. Build Artefact') {
            steps {
                sh '''
                    set -e

                    echo "Creating build artefact..."
                    rm -rf dist
                    mkdir -p dist

                    tar -czf dist/${APP_NAME}-build-${BUILD_NUMBER}.tar.gz \
                        app.py requirements.txt Dockerfile tests || true

                    echo "Build artefact created:"
                    ls -la dist
                '''
            }
        }

        stage('5. Run Automated Tests') {
            steps {
                sh '''
                    set -e
                    . ${VENV_DIR}/bin/activate

                    echo "Setting PYTHONPATH to workspace so tests can import app.py"
                    export PYTHONPATH=$WORKSPACE

                    echo "Running pytest..."
                    pytest -q --junitxml=test-results.xml

                    echo "✅ Tests completed"
                '''
            }
        }

        // ✅ NEW STAGE: Install Sonar Scanner CLI automatically
        stage('6A. Install SonarScanner CLI') {
            steps {
                sh '''
                    set -e

                    echo "Installing SonarScanner CLI locally in workspace..."

                    mkdir -p .sonar

                    if [ ! -d "${SONAR_SCANNER_DIR}" ]; then
                        echo "Downloading SonarScanner..."
                        curl -L -o .sonar/sonar-scanner.zip \
                          "https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-${SONAR_SCANNER_VERSION}-macosx.zip"

                        unzip -o .sonar/sonar-scanner.zip -d .sonar

                        # rename extracted folder to consistent path
                        mv .sonar/sonar-scanner-${SONAR_SCANNER_VERSION}-macosx ${SONAR_SCANNER_DIR}
                    else
                        echo "SonarScanner already exists in workspace. Skipping download."
                    fi

                    chmod +x ${SONAR_SCANNER_DIR}/bin/sonar-scanner
                    ${SONAR_SCANNER_DIR}/bin/sonar-scanner --version
                '''
            }
        }

        stage('6. Code Quality Analysis (SonarCloud)') {
            steps {
                script {
                    echo "Running SonarCloud scan..."
                    withCredentials([string(credentialsId: 'SONAR_TOKEN_NEW', variable: 'SONAR_TOKEN')]) {
                        sh '''
                            set -e

                            echo "Running sonar scan..."
                            ${SONAR_SCANNER_DIR}/bin/sonar-scanner \
                              -Dsonar.projectKey=${SONAR_PROJECT_KEY} \
                              -Dsonar.organization=${SONAR_ORG} \
                              -Dsonar.host.url=${SONAR_HOST_URL} \
                              -Dsonar.login=$SONAR_TOKEN
                        '''
                    }
                }
            }
        }

        stage('7. Security Analysis') {
            steps {
                sh '''
                    set -e
                    . ${VENV_DIR}/bin/activate

                    echo "Running Bandit security scan..."
                    bandit -r . -f json -o bandit-report.json || true
                    bandit -r . -f txt -o bandit-report.txt || true

                    echo "Running pip-audit dependency scan..."
                    pip-audit -f json -o pip-audit-report.json || true

                    echo "✅ Security scanning completed"
                    ls -la *.json *.txt || true
                '''
            }
        }

        stage('8. Deploy to Test Environment (Docker)') {
            steps {
                sh '''
                    set -e

                    echo "Building Docker image..."
                    docker --version
                    docker build -t ${DOCKER_IMAGE} .

                    echo "Deploying to STAGING using docker-compose..."
                    if [ -f docker-compose.staging.yml ]; then
                        docker compose -f docker-compose.staging.yml up -d --build
                    else
                        echo "No docker-compose.staging.yml found, skipping compose deploy."
                    fi
                '''
            }
        }

        stage('9. Release to Production') {
            steps {
                sh '''
                    set -e

                    echo "Promoting build to production..."
                    if [ -f docker-compose.prod.yml ]; then
                        docker compose -f docker-compose.prod.yml up -d --build
                    else
                        echo "No docker-compose.prod.yml found, skipping production compose deploy."
                    fi
                '''
            }
        }

        stage('10. Monitoring & Alerting') {
            steps {
                sh '''
                    set -e
                    echo "Monitoring stage..."

                    echo "Docker running containers:"
                    docker ps || true

                    echo "Health check endpoint:"
                    curl -s -o /dev/null -w "HTTP Status: %{http_code}\\n" http://localhost:5000/health || true

                    echo "✅ Monitoring check done"
                '''
            }
        }
    }

    post {
        always {
            script {
                echo "Archiving artifacts + reports..."
                archiveArtifacts artifacts: 'dist/**', allowEmptyArchive: true
                archiveArtifacts artifacts: '*.xml,*.json,*.txt', allowEmptyArchive: true
            }
        }
        success {
            echo "✅ SUCCESS: Pipeline completed."
        }
        failure {
            echo "❌ FAILURE: Pipeline failed. Check console output."
        }
    }
}





