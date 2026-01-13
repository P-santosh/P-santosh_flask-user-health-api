pipeline {
  agent any

  options {
    timestamps()
    ansiColor('xterm')
  }

  environment {
    // Docker image names
    IMAGE_NAME = "flask-user-health-api"
    STAGING_TAG = "staging"
    PROD_TAG = "prod"

    // SonarCloud settings (you already created these)
    SONAR_ORG = "P-santosh"
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
          docker build -t ${IMAGE_NAME}:${BUILD_NUMBER} .
        '''
      }
    }

    stage('Test') {
      steps {
        sh '''
          set -euxo pipefail
          python3.10 -m venv .venv
          . .venv/bin/activate
          pip install -r requirements-dev.txt
          pytest -q --junitxml=test-results.xml --cov=app --cov-report=xml:coverage.xml
        '''
      }
      post {
        always {
          junit allowEmptyResults: true, testResults: 'test-results.xml'
          archiveArtifacts artifacts: 'coverage.xml,test-results.xml', allowEmptyArchive: true
        }
      }
    }

    stage('Code Quality (SonarCloud)') {
      steps {
        withCredentials([string(credentialsId: 'SONAR_TOKEN', variable: 'SONAR_TOKEN')]) {
          withSonarQubeEnv('SonarCloud') {
            sh '''
              set -euxo pipefail
              SCANNER_HOME=$(tool 'SonarScanner')
              ${SCANNER_HOME}/bin/sonar-scanner                     -Dsonar.login=${SONAR_TOKEN}                     -Dsonar.organization=${SONAR_ORG}                     -Dsonar.projectKey=${SONAR_PROJECT_KEY}                     -Dsonar.projectVersion=${BUILD_NUMBER}                     -Dsonar.python.coverage.reportPaths=coverage.xml
            '''
          }
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
          archiveArtifacts artifacts: 'bandit-report.json,pip-audit-report.json', allowEmptyArchive: true
        }
      }
    }

    stage('Security Scan (Trivy Docker Image)') {
      steps {
        sh '''
          set -euxo pipefail
          trivy image --no-progress --format json -o trivy-image-report.json ${IMAGE_NAME}:${BUILD_NUMBER} || true
        '''
      }
      post {
        always {
          archiveArtifacts artifacts: 'trivy-image-report.json', allowEmptyArchive: true
        }
      }
    }

    stage('Deploy (Staging)') {
  steps {
    sh '''
      set -euxo pipefail
      docker tag flask-user-health-api:${BUILD_NUMBER} flask-user-health-api:staging
      docker compose -f docker-compose.staging.yml up -d --build
    '''
  }
}



    stage('Monitoring (Health Check)') {
      steps {
        sh '''
          set -euxo pipefail
          # Give container a moment to start
          sleep 3
          code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5050/health || true)
          echo "Health status code: $code"
          if [ "$code" != "200" ]; then
            echo "Health check failed"
            exit 1
          fi
        '''
      }
    }

    stage('Release (Production)') {
      steps {
        sh '''
          set -euxo pipefail
          docker tag ${IMAGE_NAME}:${BUILD_NUMBER} ${IMAGE_NAME}:${PROD_TAG}
          docker compose -f docker-compose.prod.yml up -d
        '''
      }
    }
  }

  post {
    always {
      sh '''
        set +e
        docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}" || true
      '''
    }
    success {
      echo "Pipeline completed successfully: Build/Test/Quality/Security/Deploy/Monitor/Release"
    }
    failure {
      echo "Pipeline failed. Check stage logs; monitoring/quality/security may have surfaced issues."
    }
    cleanup {
      sh '''
        set +e
        # keep staging/prod running (assignment demo). Uncomment if you want auto-clean:
        # docker compose -f docker-compose.staging.yml down
        # docker compose -f docker-compose.prod.yml down
        true
      '''
    }
  }
}
