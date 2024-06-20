include .env
export

all: docker-build docker-run docker-push

local-run:
	python lambda_function.py --local

local-run-with-zapier:
	python main.py --local

docker-build:
	docker build -t $(IMAGE_NAME) --platform linux/amd64 .

docker-push:
	docker push $(IMAGE_NAME)

docker-build-and-push: docker-build docker-push

docker-run: docker-reset
	docker run -it --name tippkick-bot --platform linux/amd64 --env-file .env $(IMAGE_NAME)

docker-reset:
	docker stop tippkick-bot || echo 'No container running yet'
	docker rm tippkick-bot || echo 'No container built yet'

docker-all: docker-build-and-push docker-reset docker-run
