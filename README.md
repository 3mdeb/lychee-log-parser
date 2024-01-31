# Lychee Log Parser

Tool used to analyze [Lychee link checker](https://github.com/lycheeverse/lychee)
logs. Evaluates whether the problems detected by lychee are actual site or
server problems.


## Installation

Create new python virtual environment.

``` bash
$ virtualenv venv
```

Activate virtual environment.

```bash
$ source venv/bin/activate
```

Install requirements.

```bash
pip install -r requirements.txt
```

## Usage

```
positional arguments:
  error_codes           error codes that trigger failure, in the form of an integer, a list of integers, or a range (e.g., 10..200) Example: 503 400..404 999

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         Increase logs verbosity level
  -t, --ignore-timeouts
                        Ignore timeouts
  -n, --ignore-nocode-net-err
                        Ignore network errors without status codes
  -l LOG_PATH, --log-path LOG_PATH
                        Relative path to the lychee json log file.
```
