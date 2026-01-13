pipeline {
    agent any

    environment {
        VENV_DIR   = "venv"
        PYTHON_BIN = "python3.11"
        REPORTS    = "reports"
        APP_PORT   = "5000"
        IMAGE_NAME = "my-python-app"
        DOCKER_CONTAINER_TEST = "myapp_test"
        DOCKER_CONTAINER_PROD = "myapp_prod"
    }

    options {
        timestamps()
        ansiColor('xterm')
    }

    stages {

        // 1) SCM Checkout
        stage('1. Checkout Source') {
            steps {
                echo "Checking out code from SCM..."
                checkout scm
                sh 'ls -la'
            }
        }

        // 2) Setup Environment
        stage('2. Setup Python venv') {
            steps {
                sh """
                    set -e
                    ${PYTHON_BIN} --version
                    ${PYTHON_BIN} -m venv ${VENV_DIR}
                    . ${VENV_DIR}/bin/activate
                    pip install --upgrade pip setuptools wheel
                    mkdir -p ${REPORTS}
                """
            }
        }

        // 3) Install Dependencies
        stage('3. Install Requirements') {
            steps {
                sh """
                    set -e
                    . ${VENV_DIR}/bin/activate
                    if [ -f requirements.txt ]; then
                      pip install -r requirements.txt | tee ${REPORTS}/pip_install_log.txt
                    else
                      echo "requirements.txt not found" | tee ${REPORTS}/pip_install_log.txt
                    fi
                """
            }
        }

        // 4) BUILD STAGE (Artefact)
        stage('4. Build Artefact') {
            steps {
                echo "BUILD: Creating build artefact..."
                sh """
                    set -e
                    mkdir -p dist ${REPORTS}
                    BUILD_NAME="build_\$(date +%Y%m%d_%H%M%S).zip"

                    # Create zip artefact excluding venv + git
                    zip -r dist/\$BUILD_NAME . -x "${VENV_DIR}/*" ".git/*" "dist/*" || true

                    echo "✅ Build artefact created: dist/\$BUILD_NAME" | tee ${REPORTS}/build_log.txt
                """
                archiveArtifacts artifacts: 'dist/**', allowEmptyArchive: false
            }
        }

        // 5) TEST STAGE
        stage('5. Run Automated Tests') {
            steps {
                echo "TEST: Running automated tests using PyTest..."
                sh """
                    set -e
                    . ${VENV_DIR}/bin/activate
                    pip install pytest

                    if [ -d tests ]; then
                      pytest -q --disable-warnings --maxfail=1 | tee ${REPORTS}/pytest_report.txt
                    else
                      echo "⚠️ tests folder not found. No tests executed." | tee ${REPORTS}/pytest_report.txt
                    fi
                """
            }
        }

        // 6) CODE QUALITY STAGE
        stage('6. Code Quality Analysis') {
            steps {
                echo "CODE QUALITY: Flake8 + Radon complexity check..."
                sh """
                    set -e
                    . ${VENV_DIR}/bin/activate

                    pip install flake8 radon

                    # Flake8: style + maintainability
                    flake8 . --count --statistics | tee ${REPORTS}/flake8_report.txt || true

                    # Radon: code complexity
                    radon cc . -a | tee ${REPORTS}/radon_complexity_report.txt || true

                    echo "✅ Code quality stage completed" | tee -a ${REPORTS}/code_quality_summary.txt
                """
            }
        }

        // 7) SECURITY STAGE
        stage('7. Security Analysis') {
            steps {
                echo "SECURITY: Bandit + pip-audit..."
                sh """
                    set -e
                    . ${VENV_DIR}/bin/activate

                    pip install bandit pip-audit

                    # Bandit for code security scanning
                    bandit -r . -ll -f txt | tee ${REPORTS}/bandit_report.txt || true

                    # pip-audit scans python dependencies for CVEs
                    pip-audit | tee ${REPORTS}/pip_audit_report.txt || true

                    echo "✅ Security scan completed (check reports for findings)" | tee ${REPORTS}/security_summary.txt
                """
            }
        }

        // 8) DEPLOY STAGE (Test Environment)
        stage('8. Deploy to Test Environment (Docker)') {
            steps {
                echo "DEPLOY: Deploying app to test environment using Docker..."
                sh """
                    set -e
                    docker --version

                    # Create minimal Dockerfile if not present
                    if [ ! -f Dockerfile ]; then
                      cat > Dockerfile << 'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 5000
CMD ["python", "app.py"]
EOF
                    fi

                    docker build -t ${IMAGE_NAME}:test .

                    # Stop old container if exists
                    docker rm -f ${DOCKER_CONTAINER_TEST} || true

                    docker run -d --name ${DOCKER_CONTAINER_TEST} -p ${APP_PORT}:5000 ${IMAGE_NAME}:test
                    sleep 5
                """
            }
        }

        // 9) RELEASE STAGE (Promote to Production)
        stage('9. Release to Production') {
            steps {
                echo "RELEASE: Promoting image to production tag..."
                sh """
                    set -e
                    docker tag ${IMAGE_NAME}:test ${IMAGE_NAME}:release

                    # Stop prod if exists
                    docker rm -f ${DOCKER_CONTAINER_PROD} || true

                    docker run -d --name ${DOCKER_CONTAINER_PROD} -p 5001:5000 ${IMAGE_NAME}:release
                    sleep 5
                """
            }
        }

        // 10) Monitoring and Alerting Stage
        stage('10. Monitoring & Alerting') {
            steps {
                echo "MONITORING: Checking health endpoint..."
                sh """
                    set -e
                    mkdir -p ${REPORTS}

                    # Try health endpoint if present, else just check root
                    curl -s -o /dev/null -w "%{http_code}" http://localhost:5001/health > ${REPORTS}/health_http_code.txt || true
                    CODE=\$(cat ${REPORTS}/health_http_code.txt)

                    if [ "\$CODE" = "200" ]; then
                        echo "✅ Monitoring OK: /health returned 200" | tee ${REPORTS}/monitoring_report.txt
                    else
                        echo "⚠️ Monitoring Warning: /health did not return 200 (code=\$CODE)" | tee ${REPORTS}/monitoring_report.txt
                        echo "ALERT: Application health check failed!" | tee -a ${REPORTS}/monitoring_report.txt
                    fi
                """
            }
        }
    }

    post {
        always {
            echo "Archiving Reports..."
            archiveArtifacts artifacts: 'reports/**', allowEmptyArchive: true
        }
        success {
            echo "✅ SUCCESS: Pipeline completed successfully."
        }
        failure {
            echo "❌ FAILURE: Pipeline failed. Check console + reports."
        }
    }
}


