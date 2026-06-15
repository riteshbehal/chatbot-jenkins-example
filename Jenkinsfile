pipeline {
    agent any

    options {
        timestamps()
    }

    environment {
        // Jenkins credential ID must be: dockerhub
        DOCKERHUB_CREDS = credentials('dockerhub')

        // CHANGE THIS if your DockerHub username is different
        DOCKER_NAMESPACE = 'wolfaman0'

        // DockerHub repository name to create/use
        DOCKER_REPO = 'streamlit-bedrock-chatbot'

        // Set true if you want private DockerHub repo
        DOCKER_REPO_PRIVATE = 'false'

        CONTAINER_NAME = 'streamlit-bedrock-chatbot'

        HOST_PORT = '8501'
        CONTAINER_PORT = '8501'

        AWS_REGION = 'us-east-1'
        AWS_DEFAULT_REGION = 'us-east-1'

        // Keep this as per your backend/model setup
        BEDROCK_MODEL_ID = 'amazon.nova-pro-v1:0'
    }

    stages {

        stage('Clone Repo') {
            steps {
                checkout scm

                sh '''
                    echo "Repository files:"
                    ls -la
                '''
            }
        }

        stage('Validate Files') {
            steps {
                sh '''
                    echo "Checking required chatbot files..."

                    test -f chatbot_frontend.py
                    test -f chatbot_backend.py
                    test -f requirements.txt
                    test -f Dockerfile

                    echo "Checking Python syntax..."
                    python3 -m py_compile chatbot_frontend.py
                    python3 -m py_compile chatbot_backend.py

                    echo "Validation successful."
                '''
            }
        }

        stage('Docker Login') {
            steps {
                sh '''
                    echo "Logging into DockerHub..."
                    echo "$DOCKERHUB_CREDS_PSW" | docker login -u "$DOCKERHUB_CREDS_USR" --password-stdin
                '''
            }
        }

        stage('Ensure DockerHub Repo Exists') {
            steps {
                sh '''
                    echo "Checking DockerHub repo: ${DOCKER_NAMESPACE}/${DOCKER_REPO}"

                    python3 <<'PY'
import os
import json
import sys
import urllib.request
import urllib.error

docker_user = os.environ["DOCKERHUB_CREDS_USR"]
docker_pass = os.environ["DOCKERHUB_CREDS_PSW"]
namespace = os.environ["DOCKER_NAMESPACE"]
repo = os.environ["DOCKER_REPO"]
is_private = os.environ.get("DOCKER_REPO_PRIVATE", "false").lower() == "true"

def request_json(method, url, payload=None, token=None):
    headers = {
        "Content-Type": "application/json"
    }

    if token:
        headers["Authorization"] = f"Bearer {token}"

    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        url=url,
        data=data,
        headers=headers,
        method=method
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            body = res.read().decode("utf-8")
            if body:
                return res.status, json.loads(body)
            return res.status, {}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        return e.code, {"error": body}
    except Exception as e:
        return 500, {"error": str(e)}

print(f"Authenticating with DockerHub for user: {docker_user}")

login_payload = {
    "username": docker_user,
    "password": docker_pass
}

status, login_response = request_json(
    "POST",
    "https://hub.docker.com/v2/users/login/",
    login_payload
)

if status not in [200, 201]:
    print("DockerHub API login failed.")
    print(login_response)
    sys.exit(1)

token = login_response.get("token")

if not token:
    print("DockerHub API token not received.")
    print(login_response)
    sys.exit(1)

repo_check_url = f"https://hub.docker.com/v2/namespaces/{namespace}/repositories/{repo}"

status, repo_response = request_json(
    "GET",
    repo_check_url,
    token=token
)

if status == 200:
    print(f"DockerHub repository already exists: {namespace}/{repo}")
    sys.exit(0)

if status != 404:
    print("Unable to verify DockerHub repository.")
    print(f"HTTP status: {status}")
    print(repo_response)
    sys.exit(1)

print(f"DockerHub repository not found. Creating: {namespace}/{repo}")

create_url = f"https://hub.docker.com/v2/namespaces/{namespace}/repositories"

create_payload = {
    "name": repo,
    "description": "Streamlit Bedrock chatbot deployed using Jenkins",
    "full_description": "Streamlit chatbot application deployed through Jenkins, Docker, and EC2.",
    "is_private": is_private
}

status, create_response = request_json(
    "POST",
    create_url,
    create_payload,
    token=token
)

if status in [200, 201]:
    print(f"DockerHub repository created successfully: {namespace}/{repo}")
    sys.exit(0)

print("Failed to create DockerHub repository.")
print(f"HTTP status: {status}")
print(create_response)
sys.exit(1)
PY
                '''
            }
        }

        stage('Build Image') {
            steps {
                sh '''
                    IMAGE_NAME="${DOCKER_NAMESPACE}/${DOCKER_REPO}"

                    echo "Building Docker image: ${IMAGE_NAME}:${BUILD_NUMBER}"

                    docker build \
                      -t "${IMAGE_NAME}:${BUILD_NUMBER}" \
                      -t "${IMAGE_NAME}:latest" \
                      .
                '''
            }
        }

        stage('Docker Push') {
            steps {
                sh '''
                    IMAGE_NAME="${DOCKER_NAMESPACE}/${DOCKER_REPO}"

                    echo "Pushing Docker image: ${IMAGE_NAME}:${BUILD_NUMBER}"
                    docker push "${IMAGE_NAME}:${BUILD_NUMBER}"

                    echo "Pushing Docker image: ${IMAGE_NAME}:latest"
                    docker push "${IMAGE_NAME}:latest"
                '''
            }
        }

        stage('Deploy Container') {
            steps {
                sh '''
                    IMAGE_NAME="${DOCKER_NAMESPACE}/${DOCKER_REPO}"

                    echo "Stopping old container if exists..."
                    docker stop "${CONTAINER_NAME}" || true
                    docker rm "${CONTAINER_NAME}" || true

                    echo "Starting new Streamlit chatbot container..."

                    docker run -d \
                      --name "${CONTAINER_NAME}" \
                      --restart unless-stopped \
                      -p "${HOST_PORT}:${CONTAINER_PORT}" \
                      -e AWS_REGION="${AWS_REGION}" \
                      -e AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION}" \
                      -e BEDROCK_MODEL_ID="${BEDROCK_MODEL_ID}" \
                      "${IMAGE_NAME}:latest"

                    echo "Running containers:"
                    docker ps
                '''
            }
        }

        stage('Health Check') {
            steps {
                sh '''
                    echo "Waiting for Streamlit app to start..."

                    for i in $(seq 1 20); do
                        if curl -fsS "http://localhost:${HOST_PORT}/_stcore/health" > /dev/null; then
                            echo "Application is healthy."
                            exit 0
                        fi

                        echo "Waiting... attempt $i"
                        sleep 3
                    done

                    echo "Health check failed. Showing container logs:"
                    docker logs "${CONTAINER_NAME}" || true
                    exit 1
                '''
            }
        }
    }

    post {
        always {
            sh '''
                docker logout || true
            '''
        }

        success {
            echo 'Chatbot application built, pushed, and deployed successfully.'
        }

        failure {
            echo 'Pipeline failed. Check the Jenkins console output.'
        }
    }
}
