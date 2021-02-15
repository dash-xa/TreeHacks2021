#!/bin/bash
deactivate
conda activate
export FLASK_APP=server.py
flask run
