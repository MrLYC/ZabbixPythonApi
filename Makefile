README: README.md
	pandoc README.md -t rst > README || cat README.md > README

.PHONY: sdist
sdist: README
	python setup.py sdist

.PHONY: upload
upload: README
	python setup.py sdist upload
	git tag `python setup.py --version`

.PHONY: test
test:
	env PYTHONPATH=. py.test -v tests
