import sys
import os

# set input & output directory
input_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), sys.argv[1])
output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), sys.argv[2])

# check if input & output directories are valid direcotories
for d in [input_dir, output_dir]:
    if not os.path.isdir(d):
        print("Invalid directory:\n'%s' is not a valid direcotry, please insert a valid directory name in current path." %d)
