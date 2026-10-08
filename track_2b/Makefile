IMAGE ?= apertus-sovereign-operations-bridge:judge
PORT ?= 8080
CONTAINER ?= apertus-judge
APERTUS_MODE ?= live
export APERTUS_MODE

.PHONY: build run demo
build:
	docker build -t $(IMAGE) .

run: build
	docker run --rm --name $(CONTAINER) -p 127.0.0.1:$(PORT):8080 -e APERTUS_MODE -e LLM_NAME -e LLM_BASE_URL -e LLM_API_KEY -e APERTUS_MODEL -e APERTUS_BASE_URL -e APERTUS_API_KEY $(IMAGE)

demo:
	$(MAKE) run APERTUS_MODE=mock
