# Streamlit Bedrock Chatbot with Jenkins CI/CD

This repository contains a Streamlit chatbot application powered by AWS Bedrock and LangChain. It is customized from the old Flask portfolio pipeline into a chatbot deployment pipeline.

## What Changed from the Flask App

- Removed the Flask runtime flow.
- Added Streamlit frontend: `chatbot_frontend.py`.
- Added Bedrock/LangChain backend: `chatbot_backend.py`.
- Updated Docker to run Streamlit on port `8501` instead of Flask on port `5000`.
- Updated Jenkins pipeline to build, push, and deploy the chatbot container.

## Project Structure

```text
.
├── chatbot_backend.py
├── chatbot_frontend.py
├── requirements.txt
├── Dockerfile
├── Jenkinsfile
├── .dockerignore
├── .gitignore
├── .env.example
└── README.md
```

## Prerequisites

### 1. EC2/Jenkins Server

Your Jenkins server should already have:

- Jenkins running
- Docker installed and running
- Jenkins user allowed to run Docker commands
- Git installed
- Port `8501` opened in the EC2 security group

If Docker permission fails on Amazon Linux, run:

```bash
sudo usermod -aG docker jenkins
sudo systemctl restart jenkins
```

Then log out/in or restart the EC2 instance if needed.

### 2. AWS Bedrock Access

Recommended production setup:

1. Attach an IAM role to the EC2 instance where Jenkins runs.
2. Give the role permission to call Bedrock runtime.
3. Enable access to the selected Bedrock model in the AWS console.
4. Set the correct region in `Jenkinsfile`.

The application uses the standard AWS credential provider chain. That means it can use an EC2 IAM role, environment variables, or a local AWS profile.

### 3. Jenkins DockerHub Credential

Create a Jenkins credential:

1. Go to **Manage Jenkins**.
2. Open **Credentials**.
3. Select **Global credentials**.
4. Add **Username with password**.
5. Set ID as:

```text
DockerHub
```

Use your DockerHub username and DockerHub access token/password.

## Important Jenkinsfile Edits Before Running

Open `Jenkinsfile` and change this line:

```groovy
IMAGE_NAME = 'your-dockerhub-username/streamlit-bedrock-chatbot'
```

Example:

```groovy
IMAGE_NAME = 'jitin/streamlit-bedrock-chatbot'
```

Also confirm these values:

```groovy
AWS_REGION = 'us-east-1'
AWS_DEFAULT_REGION = 'us-east-1'
BEDROCK_MODEL_ID = 'amazon.nova-pro-v1:0'
HOST_PORT = '8501'
```

## Run Locally Without Docker

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

export AWS_REGION=us-east-1
export AWS_DEFAULT_REGION=us-east-1
export BEDROCK_MODEL_ID=amazon.nova-pro-v1:0

streamlit run chatbot_frontend.py --server.port=8501
```

Open:

```text
http://localhost:8501
```

## Run Locally With Docker

```bash
docker build -t streamlit-bedrock-chatbot .

docker run -d \
  --name streamlit-bedrock-chatbot \
  -p 8501:8501 \
  -e AWS_REGION=us-east-1 \
  -e AWS_DEFAULT_REGION=us-east-1 \
  -e BEDROCK_MODEL_ID=amazon.nova-pro-v1:0 \
  streamlit-bedrock-chatbot
```

Open:

```text
http://localhost:8501
```

## Jenkins Pipeline Flow

The `Jenkinsfile` performs these stages:

1. **Checkout Code**: Pulls the latest code from GitHub.
2. **Validate Python Files**: Checks Python syntax.
3. **Build Docker Image**: Builds the chatbot Docker image.
4. **Push to DockerHub**: Pushes both build-number and latest tags.
5. **Deploy on EC2**: Stops the old container and starts the new chatbot container.

## GitHub Upload Steps

From your local project folder:

```bash
git init
git add .
git commit -m "Add Streamlit Bedrock chatbot Jenkins pipeline"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

## Jenkins Job Setup

1. Open Jenkins.
2. Create a new **Pipeline** job.
3. Select **Pipeline script from SCM**.
4. Choose **Git**.
5. Paste your GitHub repository URL.
6. Branch: `main` or `master`, depending on your repo.
7. Script path: `Jenkinsfile`.
8. Save.
9. Click **Build Now**.

After a successful build, open:

```text
http://<EC2_PUBLIC_IP>:8501
```

## Common Issues

### Docker permission denied

Run:

```bash
sudo usermod -aG docker jenkins
sudo systemctl restart jenkins
```

### Cannot access chatbot in browser

Check EC2 security group inbound rules and allow TCP `8501` from your IP.

### Bedrock credential error

Check that the EC2 IAM role has Bedrock permissions, the model is enabled, and the AWS region is correct.

### Port already in use

The Jenkins deployment stage removes the old container first. If you still face issues, run:

```bash
docker ps
docker rm -f streamlit-bedrock-chatbot
```
