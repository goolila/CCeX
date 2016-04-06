import sys
import os

# check if 2 arguments passed
try:
    arg1 = sys.argv[1]
    arg2 = sys.argv[2]
except IndexError:
    print "Usage: \tpython ccex.py <input_directory_name> <output_directory_name>"
    sys.exit(1)

# set input & output directories
input_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), arg1)
output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), arg2)

# check if input & output directories are valid direcotories
for d in [input_dir, output_dir]:
    if not os.path.isdir(d):
        print("Invalid directory:\n'%s' is not a valid direcotry, please insert a valid directory name in current path." %d)
        sys.exit(1)

def check_permission(input_dir, output_dir):
    """
    checks if input is readable and output is writeable
    """
    if not(os.access(output_dir, os.W_OK)):
        os.chmod(output_dir, int(0777))
    if not(os.access(input_dir, os.R_OK)):
        os.chmod(input_dir, int(0744))

files = os.listdir(input_dir)

for f in files:
    # f = 1-s2.0-S157082680400006X-full.xml
    f_name, f_extension = os.path.splitext(f)
    print f_name, f_extension
    if (f_extension == ".xml" and f_name[-5:] == "-full"):
        eid = f_name[0:-5] #1-s2.0-S157082680300009X
        f_path = input_dir + f
        print("Processing %s" %f_path)

# Initialize counters
number_of_papers = 0
papers_with_no_crossrefs = 0

if __name__ == "__main__":
    # set and check input & output directories
    check_permission(input_dir, output_dir)
    # print ("Input: %s\t is OK\nOutput: %s\tis OK" %(input_dir, output_dir))
