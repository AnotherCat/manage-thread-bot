# Thread Manager

This bot was made to be an internal helper for a staff server  
It auto un-archives a thread that is set to "Keep alive" and will send a poll after a specified time of inactivity.  

## Installation

### Prequisits

- Python 3.9
- Pipenv

### Steps

- Set config
    - Rename `config.example.py` to `config.py`
    - Set values
- Run `pipenv sync`
- Run `aerich upgrade`
- Run `python main.py`
