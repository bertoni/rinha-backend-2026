dev:
	export OMP_NUM_THREADS=1
	export MKL_NUM_THREADS=1
	export OPENBLAS_NUM_THREADS=1
	export NUMEXPR_NUM_THREADS=1
	uvicorn main:app --reload --host 0.0.0.0 --port 8080

venv/create:
	python -m venv .venv

venv/activate:
	source .venv/bin/activate

update_dependencies:
	pip freeze > requirements.txt