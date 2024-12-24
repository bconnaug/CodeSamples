Code Samples
Author: Belle Connaught

This folder contains two standalone files from two larger projects, showcasing 
my coding skills and problem-solving abilities. Below is an explanation of what
each file does and how they demonstrate my abilities.

# 1. File Name: `lsp_server.go` 
This file contains my implementation of an LSP server for a distributed Bitcoin
mining system, written in Golang for my Distributed Systems class. 
It utilizes the lsp package to handle reliable communication with clients and miners. 

Key functionalities include:
    - Distributing mining jobs to available miners using a round-robin-like approach.
    - Managing client requests by splitting large mining ranges into smaller chunks.
    - Handling miner and client disconnections gracefully by reassigning tasks.
    - Aggregating and returning the lowest hash result from miners to clients.

This server ensures fair job distribution and efficient recovery mechanisms to maintain 
system reliability.

# 2. File Name: `findDrumstick.py`
This Python file is a core component of DrumLite (my senior capstone project), a 
portable drumset that uses a webcam and accelerometer-based system to detect 
drumstick hits and trigger corresponding sounds. 

This file is responsible for tracking the drumstick tips in real-time, using computer 
vision. It utilizes OpenCV to process video frames from the webcam and applies 
HSV color masking to detect drumstick tips (colored blue and green). 
The detection logic runs in separate threads for each drumstick as well, with
color thresholds adjusted dynamically based on each drumstick tip's color. 

`findDrumstick.py` also performs contour detection to identify and track the position 
of each drumstick tip across frames, ensuring accurate hit detection by matching
the tip's location to one of the drum pads. 

This setup allows for responsive drumstick tracking in a portable, low-latency 
environment, making DrumLite both accessible and effective for interactive drumming.
