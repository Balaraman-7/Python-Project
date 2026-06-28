#!/bin/bash

# Install dependencies
pip install -r requirements.txt

# Collect static files for WhiteNoise / Vercel static serving
python manage.py collectstatic --noinput
