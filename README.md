# public-api
structure:
- src: contains all program files
- src.api: contains the api
- src.app: contains the database logic
- src.core: contains the core componetns
- src.core.database: contains all the database functionality

# setup
## windows
creating a python venv to work in and install the project requirements
```sh
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pre-commit install
```
## linux
use the `make` command with an `action` when developing on linux.  think of `actions` as a list of predefined commands to help simplify common development routines.

#### view avaiable actions
`make help` to see all avaiable actions

```sh
public-api$ make help
clean-pyc            clean python cache files
clean-test           cleanup pytests leftovers
test                 Run pytest unit tests
test-debug           Run unit tests with debugging enabled
test-coverage        Run unit tests and check code coverage
docker-up            Startup docker
docker-build         Startup docker
setup                setup & run after downloaded repo
pre-commit-setup     Install pre-commit
pre-commit           Run pre-commit
```

### setup your enviornment
prereqs: 
- docker
- python3
- local clone of repo
- terminal opened to cloned repos root path

run `setup`
```sh
public-api$ make setup
```

once complete you will have to open a new terminal as the docker output will be running in the current one. you are looking for the message 'Application startup complete.' to know when the `setup` is done and containers are running. 

more explinations of different `make` `actions` that can be run in the other sections below

#### take docker conters down

run `docker-down`

```sh
public-api$ make docker-down
docker-compose down
[+] Running 6/6
 ✔ Container kafdrop                       Removed  10.2s 
 ✔ Container public_api                    Removed   0.4s 
 ✔ Container kafka_setup                   Removed   0.0s 
 ✔ Container database                      Removed   0.8s 
 ✔ Container kafka                         Removed   0.9s 
 ✔ Network public-api_botdetector-network  Removed   0.0s 
```

### bring docker containers back up
run `docker-up`. example below is using public-api
```sh
public-api$ make docker-up
docker-compose --verbose up
[+] Building 0.0s (0/0)                              
[+] Running 7/5
 ✔ Network public-api_botdetector-Network
 ✔ Container database kafka_setup                   
 ✔ Container kafka
 ✔ Container kafka_setup 
 ✔ Container kafdrop
 ...
 ...
 public_api   | INFO:     Application startup complete.
 ...
```

### force rebuild of containers
run `docker-force-rebuild`. usually done if requirements.txt are changed.  or if containers are having weird issues and you want to start fresh.

```sh
public-api$ make docker-force-rebuild
```

### make sure tests are still passing
run `test`

```sh
public-api$ make test

python3 -m pytest --verbosity=1 --rootdir=./
=============== test session starts ===============
platform darwin -- Python 3.11.6, pytest-7.4.2, pluggy-1.3.0 -- /opt/homebrew/opt/python@3.11/bin/python3.11
cachedir: .pytest_cache
hypothesis profile 'default' -> database=DirectoryBasedExampleDatabase(PosixPath('./bot-detector/public-api/.hypothesis/examples'))
rootdir: public-api
plugins: hypothesis-6.88.1, anyio-3.7.1
collected 13 items                   

tests/test_player_api.py::TestPlayerAPI::test_invalid_player_returns_empty PASSED             [  7%]
tests/test_player_api.py::TestPlayerAPI::test_invalid_player_returns_success PASSED           [ 15%]
tests/test_player_api.py::TestPlayerAPI::test_valid_player_returns_data PASSED       [ 23%]
tests/test_player_api.py::TestPlayerAPI::test_valid_player_returns_success PASSED             [ 30%]
tests/test_prediction_api.py::TestPredictionAPI::test_invalid_max_player_name_length_returns_unkonwn PASSED     [ 38%]
tests/test_prediction_api.py::TestPredictionAPI::test_invalid_min_player_name_length_returns_unknown PASSED     [ 46%]
tests/test_prediction_api.py::TestPredictionAPI::test_invalid_player_breakdown_false_returns_player_not_found PASSED     [ 53%]
tests/test_prediction_api.py::TestPredictionAPI::test_invalid_player_breakdown_true_returns_player_not_found PASSED      [ 61%]
tests/test_prediction_api.py::TestPredictionAPI::test_invalid_player_breakdown_true_returns_unknown PASSED      [ 69%]
tests/test_prediction_api.py::TestPredictionAPI::test_valid_player_breakdown_false_returns_empty_property PASSED         [ 76%]
tests/test_prediction_api.py::TestPredictionAPI::test_valid_player_breakdown_false_returns_success PASSED       [ 84%]
tests/test_prediction_api.py::TestPredictionAPI::test_valid_player_breakdown_true_returns_populated_property PASSED      [ 92%]
tests/test_prediction_api.py::TestPredictionAPI::test_valid_player_breakdown_true_returns_success PASSED        [100%]

=============== 13 passed in 1.54s ===============
```
# for admin purposes saving & upgrading
when you added some dependancies update the requirements
```sh
.venv\Scripts\activate
call pip freeze > requirements.txt
```
when you want to upgrade the dependancies
```sh
.venv\Scripts\activate
powershell "(Get-Content requirements.txt) | ForEach-Object { $_ -replace '==', '>=' } | Set-Content requirements.txt"
call pip install -r requirements.txt --upgrade
call pip freeze > requirements.txt
powershell "(Get-Content requirements.txt) | ForEach-Object { $_ -replace '>=', '==' } | Set-Content requirements.txt"
```