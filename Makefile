consul-up:
	docker-compose -f ./consul.yml up

consul-down:
	docker-compose -f ./consul.yml down

app-build:
	docker-compose -f ./app.yml build

app-up:
	docker-compose -f ./app.yml up

app-down:
	docker-compose -f ./app.yml down

all:
	docker-compose -f ./consul.yml -f ./app.yml up