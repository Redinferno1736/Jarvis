#!/bin/bash
# Create a directory for FFmpeg
mkdir -p ffmpeg

# Download a prebuilt static FFmpeg binary
curl -L https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz | tar -xJ --strip-components=1 -C ffmpeg
