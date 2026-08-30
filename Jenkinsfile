pipeline {
    agent any

    environment {
        PYTHONUNBUFFERED = "1"
        APP_VERSION = "${env.TAG_NAME ?: env.BRANCH_NAME ?: 'v1.0.0'}"
    }

    stages {
        stage('Checkout Source') {
            steps {
                checkout scm
            }
        }

        stage('Set Up Environment & Dependencies') {
            steps {
                sh '''
                    python3 -m venv .venv
                    . .venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Execute Pytest Suite & Regression Tests') {
            steps {
                sh '''
                    . .venv/bin/activate
                    pytest -v --junitxml=reports/pytest-report.xml
                '''
            }
        }

        stage('Build Versioned Docker Image') {
            steps {
                sh """
                    docker build -t ceb-ledger:${APP_VERSION} -t ceb-ledger:latest .
                    echo "Built Docker image tagged: ceb-ledger:${APP_VERSION}"
                """
            }
        }
    }

    post {
        always {
            cleanWs()
        }
        success {
            echo "CEB-Ledger ${APP_VERSION} build & test pipeline completed successfully."
        }
        failure {
            echo "CEB-Ledger build failed for version ${APP_VERSION}."
        }
    }
}
