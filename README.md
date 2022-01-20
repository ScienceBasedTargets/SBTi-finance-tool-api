> Visit  http://getting-started.sbti-tool.org/ for the full documentation

> If you have any additional questions or comments send a mail to: finance@sciencebasedtargets.org

# SBTi Temperature Alignment tool API
This package helps companies and financial institutions to assess the temperature alignment of current
targets, commitments, and investment and lending portfolios, and to use this information to develop 
targets for official validation by the SBTi.

Under the hood, this API uses the SBTi Python module. The complete structure that consists of a Python module, API and a UI looks as follows:

    +-------------------------------------------------+
    |   UI     : Simple user interface on top of API  |
    |   Install: via dockerhub                        |
    |            docker.io/sbti/ui:latest             |
    |                                                 |
    | +-----------------------------------------+     |
    | | REST API: Dockerized FastAPI/NGINX      |     |
    | | Source : github.com/OFBDABV/SBTi_api    |     |
    | | Install: via source or dockerhub        |     |
    | |          docker.io/sbti/sbti/api:latest |     |
    | |                                         |     |
    | | +---------------------------------+     |     |
    | | |                                 |     |     |
    | | |Core   : Python Module           |     |     |
    | | |Source : github.com/OFBDABV/SBTi |     |     |
    | | |Install: via source or PyPi      |     |     |
    | | |                                 |     |     |
    | | +---------------------------------+     |     |
    | +-----------------------------------------+     |
    +-------------------------------------------------+

Note that one can deploy the api also including a User interface. This repo depends on a docker image 
(docker.io/sbti/ui:latest) that can be spinned up if necessary, see instruction in the deployment section.

## Structure
The folder structure for this project is as follows:

    .
    ├── .github                 # Github specific files (Github Actions workflows)
    ├── app                     # FastAPI app files for the API endpoints
    └── config                  # Config files for the Docker container

## Deployment
This service can be deployed in two ways, either as a standalone API or in conjunction with a no-frills UI.
For both of these options a docker configuration has been set up. 

In order to run the docker container locally or non linux machines one needs to install [Docker Desktop](https://www.docker.com/products/docker-desktop) available for Mac and Windows

### API-only
The master branch of this repo has a public image at Dockerhub. To run them, use the following commands: 

```bash
docker run -d -p 5000:8080 sbti/api:latest # to run  the latest stable release
```
In order to run a locally build version run:

```bash
docker-compose up --build
```

The API swagger documentation should now be available at [http://localhost:5000/docs/](http://localhost:5000/docs/).

### API and UI
To launch both the API and the UI, you need to use the provided docker-compose files.
This will spin up two containers that work in conjunction with one another.

To launch the latest release:
```bash
docker-compose -f docker-compose-ui.yml up -d --build
``` 

To use your local code-base:
```bash
docker-compose -f docker-compose-ui-dev.yml up -d --build
``` 

The UI should now be available at [http://localhost:5000/](http://localhost:5000/) and check [http://localhost:5001/docs/](http://localhost:5001/docs/) for the API documentation

To build an run the docker container locally use the following command:
```bash
docker-compose up -d --build
```

## Deploy on Amazon Web Services
These instructions assume that you've installed and configured the Amazon [AWS CLI tools](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html) and the [ECS CLI tools](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ECS_CLI_Configuration.html) with an IAM account that has at least write access to ECS and EC2 and the capability of creating AIM roles.

1. Configure the cluster. You can update the region and names as you see fit
```bash
ecs-cli configure --cluster sbti-ecs-cluster --region eu-central-1 --config-name sbti-ecs-conf --cfn-stack-name sbti-ecs-stack --default-launch-type ec2
```
2. Create a new key pair. The result of this command is a key. Store this safely as you can later use it to access your instance through SSH.
```bash
aws ec2 create-key-pair --key-name sbti
```
3. Create the instance that'll run the image. Here we used 1 server of type t2.medium. Change this as you see fit.
```bash
ecs-cli up --keypair sbti --capability-iam --size 1 --instance-type t2.medium --cluster-config sbti-ecs-conf
```
4. Update the server and make it run the docker image.
```bash
ecs-cli compose -f docker-compose_aws.yml up --cluster-config sbti-ecs-conf
```
5. Now that the instance is running we can't access it yet. That's because NGINX only listens to localhost. We need to change this to make sure it's accessible on the WWW.
6. Login to the Amazon AWS console
7. Go to the EC2 service
8. In the instance list find the instance running the Docker image
9. Copy the public IP address of the instance
10. In ```config/api-nginx.conf``` update the server name to the public IP.
11. Now we need to rebuild and re-upload the image.
```bash
docker-compose -f docker-compose_aws.yml build --no-cache
docker-compose -f docker-compose_aws.yml push
ecs-cli compose -f docker-compose_aws.yml up --cluster-config sbti-ecs-conf --force-update
```
12. You should now be able to access the API.

> :warning: This will make the API publicly available on the world wide web! Please note that this API is not protected in any way. Therefore it's recommended to run your instance in a private subnet and only access it through there. Alternatively you can change the security group settings to only allow incoming connections from your local IP or company VPN.  

## Development

To set up the local dev environment with all dependencies, [install poetry](https://python-poetry.org/docs/#osx--linux--bashonwindows-install-instructions) and run

```bash
poetry install
```

This will create a virtual environment inside the project folder under `.venv`.

### Updating Dependencies

always run `poetry export -f requirements.txt --output requirements.txt --without-hashes` after updating a dependency to keep the `requirements.txt` file up to date as well.