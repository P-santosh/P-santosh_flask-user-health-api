pipeline {
  agent any

  options {
    timestamps()
    ansiColor('xterm')
    timeout(time: 15, unit: 'MINUTES')
  }

  environment {
    // Apple Silicon Homebrew paths
    DOCKER = "/opt/homebrew/bin/docker"
    TRIVY  = "/opt/homebrew/bin/trivy"

    // Docker image name
    IMAGE_NAME = "flask-user-health-api"
    IMAGE_TAG  = "${BUILD_NUMBER}"

    // SonarCloud settings
    SONAR_HOST_URL    = "https://sonarcloud.io"
    SONAR_ORG         = "p-santosh"
    SONAR_PROJECT_KEY = "P-santosh_flask-user-health-api"
  }

  stages {

    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Build') {
      steps {
        sh '''
          set -euxo pipefail
          ${DOCKER} --version
          ${DOCKER} build -t ${IMAGE_NAME}:${IMAGE_TAG} .
        '''
      }
    }

    stage('Test') {
      steps {
        sh '''
          set -euxo pipefail

          python3.10 -m venv .venv
          . .venv/bin/activate

          pip install --upgrade pip
          pip install -r requirements-dev.txt

          pytest -q --junitxml=test-results.xml --cov=app --cov-report=xml:coverage.xml || true

          ls -la
        '''
      }
      post {
        always {
          junit allowEmptyResults: true, testResults: 'test-results.xml'
          archiveArtifacts allowEmptyArchive: true, artifacts: 'test-results.xml,coverage.xml'
        }
      }
    }

    stage('Code Quality (SonarCloud)') {
      steps {
        withCredentials([string(credentialsId: 'SONAR_TOKEN', variable: 'SONAR_TOKEN')]) {
          sh '''
            set -euxo pipefail

            # Run Sonar Scanner container
            ${DOCKER} run --rm \
              -e SONAR_TOKEN=$SONAR_TOKEN \
              -v "$PWD:/usr/src" \
              sonarsource/sonar-scanner-cli:latest \
              -Dsonar.host.url=${SONAR_HOST_URL} \
              -Dsonar.organization=${SONAR_ORG} \
              -Dsonar.projectKey=${SONAR_PROJECT_KEY} \
              -Dsonar.projectVersion=${IMAGE_TAG} \
              -Dsonar.python.coverage.reportPaths=coverage.xml
          '''
        }
      }
    }

    stage('Security Scan (Bandit + pip-audit)') {
      steps {
        sh '''
          set -euxo pipefail

          . .venv/bin/activate

          bandit -r . -x .venv,tests -f json -o bandit-report.json || true
          pip-audit -r requirements.txt -f json -o pip-audit-report.json || true
        '''
      }
      post {
        always {
          archiveArtifacts allowEmptyArchive: true, artifacts: 'bandit-report.json,pip-audit-report.json'
        }
      }
    }

    stage('Security Scan (Trivy Docker Image)') {
      steps {
        sh '''
          set -euxo pipefail

          # Trivy should be installed on host
          ${TRIVY} --version

          ${TRIVY} image --no-progress --format json -o trivy-image-report.json ${IMAGE_NAME}:${IMAGE_TAG} || true
        '''
      }
      post {
        always {
          archiveArtifacts allowEmptyArchive: true, artifacts: 'trivy-image-report.json'
        }
      }
    }

    stage('Deploy (Staging)') {
      steps {
        sh '''
          set -euxo pipefail

          ${DOCKER} tag ${IMAGE_NAME}:${IMAGE_TAG} ${IMAGE_NAME}:staging
          ${DOCKER} compose -f docker-compose.staging.yml up -d
        '''
      }
    }

    stage('Monitoring (Health Check)') {
      steps {
        sh '''
          set -euxo pipefail

          echo "Waiting for service..."
          sleep 5

          # Update this URL if your staging runs on different port
          curl -fsS http://localhost:5000/health
        '''
      }
    }

    stage('Release (Production)') {
      steps {
        sh '''
          set -euxo pipefail

          ${DOCKER} tag ${IMAGE_NAME}:${IMAGE_TAG} ${IMAGE_NAME}:prod
          ${DOCKER} compose -f docker-compose.prod.yml up -d
        '''
      }
    }

  } // end stages

  post {
    always {
      sh '''
        set +e
        echo "=== Running containers ==="
        ${DOCKER} ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}" || true
        true
      '''
    }

    success {
      echo "✅ Pipeline finished SUCCESSFULLY"
    }

    failure {
      echo "❌ Pipeline failed - check stage logs above"
    }
  }
}

