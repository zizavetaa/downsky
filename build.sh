#!/bin/bash

# Update package index
apt-get update

# Install SDL2 dependencies
# Source - https://stackoverflow.com/a/60990677
# Posted by EakzIT, modified by community. See post 'Timeline' for change history
# Retrieved 2026-04-22, License - CC BY-SA 4.0

apt-get install python-dev libsdl-image1.2-dev libsdl-mixer1.2-dev libsdl-ttf2.0-dev libsdl1.2-dev libsmpeg-dev python-numpy subversion libportmidi-dev ffmpeg libswscale-dev libavformat-dev libavcodec-dev libfreetype6-dev

echo "INSTALLED"

# Install Python dependencies from requirements.txt
pip install -r requirements.txt
