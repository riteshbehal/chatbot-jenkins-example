pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    environment {
        // IMPORTANT: Replace this with your DockerHub username/repository before pushing to GitHub.
        IMAGE_NAME = 'your-dockerhub-username/streamlit-bedrock-chatbot'

        // Jenkins credential ID for DockerHub username/password.
        // Create it in Jenkins as: Manage Jenkins -> Credentials -> Global -> Username with password.
        DOCKERHUB_CREDENTIALS = credentials('DockerHub')

        CONTAINER_NAME = 'streamlit-bedrock-chatbot'
        APP_PORT = '8501'
        HOST_PORT = '8501'

        // Change this if your Bedrock model is enabled in another AWS region.
        AWS_REGION = 'us-east-1'
        AWS_DEFAULT_REGION = 'us-east-1'
        BEDROCK_MODEL_ID = 'amazon.nova-pro-v1:0'
    }

    stages {
        stage('Checkout Code') {
            steps {
                checkout scm
            }
        }

        stage('Validate Python Files') {
            steps {
                sh '''
                    set -e
                    python3 -m py_compile chatbot_backend.py chatbot_frontend.py
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                sh '''
                    set -e
                    docker build \
                      -t ${IMAGE_NAME}:${BUILD_NUMBER} \
                      -t ${IMAGE_NAME}:latest \
                      .
                '''
            }
        }

        stage('Push to DockerHub') {
            steps {
                sh '''
                    set -e
                    echo "${DOCKERHUB_CREDENTIALS_PSW}" | docker login -u "${DOCKERHUB_CREDENTIALS_USR}" --password-stdin
                    docker push ${IMAGE_NAME}:${BUILD_NUMBER}
                    docker push ${IMAGE_NAME}:latest
                '''
            }
        }

        stage('Deploy on EC2') {
            steps {
                sh '''
                    set -e
                    docker rm -f ${CONTAINER_NAME} || true

                    docker run -d \
                      --name ${CONTAINER_NAME} \
                      --restart unless-stopped \
                      -p ${HOST_PORT}:${APP_PORT} \
                      -e AWS_REGION=${AWS_REGION} \
                      -e AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION} \
                      -e BEDROCK_MODEL_ID=${BEDROCK_MODEL_ID} \
                      ${IMAGE_NAME}:${BUILD_NUMBER}

                    docker image prune -f
                '''
            }
        }
    }

    post {
        success {
            echo '✅ Build, Docker push, and EC2 deployment completed successfully.'
            echo "🌐 Open the chatbot at: http://<YOUR_EC2_PUBLIC_IP>:${HOST_PORT}"
        }
        failure {
            echo '❌ Pipeline failed. Check the Jenkins console logs.'
        }
        always {
            sh 'docker logout || true'
        }
    }
}
