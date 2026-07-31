export FLASK_ENV="development"
export FLASK_DEBUG="1"
source $(poetry env info --path)/bin/activate
flask run --reload --with-threads --host=172.30.179.208 --port=27467
