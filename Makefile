.PHONY: test
test:
	env PYTHONPATH=. py.test -v tests
