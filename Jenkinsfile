pipeline {
    agent any

    environment {
        VENV_DIR = ".venv"
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Setup Python venv (Python 3.11)') {
            steps {
                sh '''
                set -e

                echo "Python version:"
                python3.11 --version

                python3.11 -m venv .venv

                . .venv/bin/activate

                python -m pip install --upgrade pip setuptools wheel
                '''
            }
        }

        stage('Install Requirements') {
            steps {
                sh '''
                set -e
                . .venv/bin/activate

                if [ -f requirements.txt ]; then
                    pip install -r requirements.txt
                fi

                # Always ensure Bandit exists
                pip install "bandit>=1.7.8"
                '''
            }
        }

        stage('Run Bandit Security Scan') {
            steps {
                sh '''
                set -e
                . .venv/bin/activate

                echo "Running Bandit scan..."

                # Scan only source code; exclude virtual env
                bandit -r . \
                  -x ".venv,./.venv,venv,__pycache__,tests" \
                  -f json \
                  -o bandit-report.json

                # Human readable output too
                bandit -r . \
                  -x ".venv,./.venv,venv,__pycache__,tests" \
                  -f txt \
                  -o bandit-report.txt
                '''
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'bandit-report.json, bandit-report.txt', allowEmptyArchive: true
        }
    }
}

