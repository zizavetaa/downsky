#!/bin/bash

# Update package index
apt-get update

# Install SDL2 dependencies
apt-get install -y \
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev \
    libsmpeg-dev \
    libportmidi-dev \
    libfreetype6-dev \
    libavformat-dev \
    libswscale-dev \
    python3-dev \
    build-essential


# Install Python dependencies from requirements.txt
pip install -r requirements.txt
