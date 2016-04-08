import sys
import os
from lxml import etree as et

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

namespaces = {'xocs' : 'http://www.elsevier.com/xml/xocs/dtd',
    'ce' : 'http://www.elsevier.com/xml/common/dtd',
    'xmlns' : "http://www.elsevier.com/xml/svapi/article/dtd",
    'xmlns:xsi' : "http://www.w3.org/2001/XMLSchema-instance",
    'xmlns:prism' : "http://prismstandard.org/namespaces/basic/2.0/",
    'xmlns:dc' : "http://purl.org/dc/elements/1.1/",
    'xmlns:xocs' : "http://www.elsevier.com/xml/xocs/dtd",
    'xmlns:xlink' : "http://www.w3.org/1999/xlink",
    'xmlns:tb' : "http://www.elsevier.com/xml/common/table/dtd",
    'xmlns:sb' : "http://www.elsevier.com/xml/common/struct-bib/dtd",
    'xmlns:sa' : "http://www.elsevier.com/xml/common/struct-aff/dtd",
    'xmlns:mml' : "http://www.w3.org/1998/Math/MathML",
    'xmlns:ja' : "http://www.elsevier.com/xml/ja/dtd",
    'xmlns:ce' : "http://www.elsevier.com/xml/common/dtd",
    'xmlns:cals' : "http://www.elsevier.com/xml/common/cals/dtd",
}

files = os.listdir(input_dir)

for f in files:
    # f = 1-s2.0-S157082680400006X-full.xml
    f_name, f_extension = os.path.splitext(f)
    print f_name, f_extension
    if (f_extension == ".xml" and f_name[-5:] == "-full"):
        eid = f_name[0:-5] #1-s2.0-S157082680300009X
        f_path = input_dir + f
        print("Processing %s" %f_path)

        tree = et.parse(f_path)

        """
        Expand cross-refs as multiple adjacent <cross-ref refid=''> elements
        """
        xpath = "//ce:cross-refs"
        cross_refs = tree.xpath(xpath, namespaces={'ce' : 'http://www.elsevier.com/xml/common/dtd'})
        for c in cross_refs:
            c_parent = c.getparent()
            ref_ids = c.attrib['refid'].strip().split()
            for r in ref_ids:
                CE = "http://www.elsevier.com/xml/common/dtd"
                NS_MAP = {'ce' : CE}
                tag = et.QName(CE, 'cross-refs')
                exploded_cross_refs = et.Element(tag, refid=r, nsmap=NS_MAP)
                # what should be .text ? [r1, r2] or just [r1]
                exploded_cross_refs.text = c.text
                c.addprevious(exploded_cross_refs)
            c_parent.remove(c)

        """
        Number bib-reference(s)
        Add an attribute to each cross-ref with the number of the bibliographic reference it denotes.
        """
        xpath_bib_references ="//ce:bib-reference"
        bib_refrences = tree.xpath(xpath_bib_references, namespaces={'ce' : 'http://www.elsevier.com/xml/common/dtd'})

		bib_ref_pos = 1
        for b in bib_refrences:
            b.set("positionNumber", bib_ref_pos)
            # how to pass variable to xpath expression?
            b_ref_id = b.attrib['id'].split()
            xpath_cross_ref_bib_pointers = "//ce:cross-ref[@refid='%s']" %b_ref_id
            cross_ref_bib_pointers = tree.xpath(xpath_cross_ref_bib_pointers, namespaces={'ce' : 'http://www.elsevier.com/xml/common/dtd'})

            for c in cross_ref_bib_pointers:
                c.set("positionNumberOfBibliographicReference", bib_ref_pos)

            bib_ref_pos += 1

        """
        Identify InTextPointer (by checking @positionNumberOfBibliographicReference attribute)
        - Add position attribute
        - Normalize cross-ref content, by substituting content with a marker
            - invokes buildTextualMarker() #what is buildTextualMarker??
        """
        xpath = "//ce:cross-ref[@positionNumberOfBibliographicReference]"
        cross_refs = tree.xpath(xpath)
        #cross_ref_info = []

        for c in cross_refs:
            current_ref_id = c.attrib["positionNumberOfBibliographicReference"]
            c_info_beind_added = []
            c_info_beind_added['positionNumber'] = c.attrib["positionNumber"]
            c_info_beind_added['positionNumberOfBibliographicReference'] = current_ref_id

            c_textual_marker_current = buildTextualMarker($currentCrossRefPosition, $crossRef->getAttribute('positionNumberOfBibliographicReference'));

# Initialize counters
number_of_papers = 0
papers_with_no_crossrefs = 0

if __name__ == "__main__":
    # set and check input & output directories
    check_permission(input_dir, output_dir)
    # print ("Input: %s\t is OK\nOutput: %s\tis OK" %(input_dir, output_dir))
