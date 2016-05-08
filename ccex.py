import os
import re
import sys
import time
import logging
import nltk.data
from lxml import etree as et
from rdflib import Graph, URIRef, Literal
from rdflib.namespace import Namespace, NamespaceManager, RDF

# language to be used by nlptk
sent_detector = nltk.data.load('tokenizers/punkt/english.pickle')

# available logging for RDF
logging.basicConfig(level=logging.INFO)

# Global variables
SEMLANCET_NS = "http://www.semanticlancet.eu/resource/"
SEMLANCET_URI_PRO_ROLE_AUTHOR = "http://purl.org/spar/pro/author"
SUMMARY_FILENAME = "CITATION_CONTEXTS_SUMMARY.csv"
RDF_EXTENSION = "ttl"
RDF_SERIALIZATION_FORMAT = "turtle"
NON_DECIMAL = re.compile(r'[^\d.]+')

# Counters
number_of_papers = 0
total_time = 0
count_remove_preserve = 0
count_remove_all = 0
papers_with_block_detect_error = []
papers_with_no_crossrefs = []

# namespaces
CE = "http://www.elsevier.com/xml/common/dtd"
NS_MAP = {'ce': CE}
cross_ref_tag_name = et.QName(CE, 'cross-ref')
cross_refs_tag_name = '{http://www.elsevier.com/xml/common/dtd}cross-refs'

# rdf namspaces
frbrNS = Namespace('http://purl.org/vocab/frbr/core#')
coNS = Namespace('http://purl.org/co/')
foafNS = Namespace('http://xmlns.com/foaf/0.1/')
c4oNS = Namespace('http://purl.org/spar/c4o/')
proNS = Namespace('http://purl.org/spar/pro/')
docoNS = Namespace('http://purl.org/spar/doco/')

ns_mgr = NamespaceManager(Graph())
ns_mgr.bind('frbr', frbrNS, override=False)
ns_mgr.bind('co', coNS, override=False)
ns_mgr.bind('foaf', foafNS, override=False)
ns_mgr.bind('c4o', c4oNS, override=False)
ns_mgr.bind('pro', proNS, override=False)
ns_mgr.bind('doco', docoNS, override=False)

# simple namespace def
c4o = Namespace('http://purl.org/spar/c4o/')
frbr = Namespace('http://purl.org/vocab/frbr/core#')
doco = Namespace('http://purl.org/spar/doco/')

NMSPCS = {'xocs' : 'http://www.elsevier.com/xml/xocs/dtd',
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

# functions
def check_permission(input_dir, output_dir):
    """
    checks if input is readable and output is writeable
    """
    if not(os.access(output_dir, os.W_OK)):
        os.chmod(output_dir, int(0777))
    if not(os.access(input_dir, os.R_OK)):
        os.chmod(input_dir, int(0744))
    print ("Input: %s\t is OK\nOutput: %s\tis OK" %(input_dir, output_dir))

def explode(c_vals, ref_ids, c, c_parent):
    i = 0
    for r in ref_ids:
        exploded_cross_refs = et.Element(cross_ref_tag_name, refid=r, nsmap=NS_MAP)
        exploded_cross_refs.set("connected", str(i))
        exploded_cross_refs.text = "[" + c_vals[i] + "]"
        c.addprevious(exploded_cross_refs)
        i += 1
    remove_cross_refs(c, c_parent)

def remove_preserve_tail(element):
    if element.tail:
        prev = element.getprevious()
        parent = element.getparent()
        if prev is not None:
            prev.tail = (prev.tail or '') + element.tail
        else:
            parent.text = (parent.text or '') + element.tail
        parent.remove(element)

def remove_cross_refs(element, element_parent):
    global count_remove_all, count_remove_preserve
    count_remove_all += 1
    try:
        et.strip_elements(element_parent, cross_refs_tag_name, with_tail=False)
    except TypeError:
        count_remove_preserve += 1
        remove_preserve_tail(element)

def build_textual_marker(p_number, ref_id):
    # output : [xxxcitxxx[[_'6'_][_'1'_]]xxxcitxxx]
    return "[xxxcitxxx[[_'" + str(p_number) + "'_][_'" + ref_id + "'_]]xxxcitxxx]"

# set/check input & output directories
try:
    arg1 = sys.argv[1]
    arg2 = sys.argv[2]
except IndexError:
    print "Usage: \tpython ccex.py <input_directory_name> <output_directory_name>"
    sys.exit(1)

input_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), arg1)
output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), arg2)

for d in [input_dir, output_dir]:
    if not os.path.isdir(d):
        print("Invalid directory:\n'%s' is not a valid direcotry, please insert a valid directory name in current path." %d)
        sys.exit(1)
check_permission(input_dir, output_dir)

files = os.listdir(input_dir)

for f in files:
    # f = 1-s2.0-S157082680400006X-full.xml
    start_time = time.time()
    f_name, f_extension = os.path.splitext(f)
    if (f_extension == ".xml" and f_name[-5:] == "-full"):
        eid = f_name[0:-5]
        f_path = input_dir + f
        print("Processing %s" %f)

        tree = et.parse(f_path)

        """
        STEP 1
        Expand cross-refs as multiple adjacent <cross-ref refid=''> elements
        - finds 'bib1' in bibliography, sets its positionNumber'1' ->
            finds all ce:cross-ref with refid = 'bib1' , set its positionNumberofBiblioref same as positionnumber'1'
        """
        xpath = "//ce:cross-refs"
        cross_refs = tree.xpath(xpath, namespaces=NS_MAP )

        for c in cross_refs:
            c_parent = c.getparent()
            c_val = c.text.strip("[]")
            if c_val:
                c_vals = re.split(',|and', c_val)
                ref_ids = c.attrib['refid'].strip().split()
                if (len(c_vals) == len(ref_ids)):
                    explode(c_vals, ref_ids, c, c_parent)
                else:
                    new_c_vals = []
                    for element in c_vals:
                        if element.isdigit():
                            new_c_vals.append(str(element))
                        else:
                            toexpand = NON_DECIMAL.sub('f', element)
                            toexpand = toexpand.split("f")
                            try:
                                for i in range(int(toexpand[0]), int(toexpand[1]) + 1, 1):
                                    new_c_vals.append(str((i)))
                            except ValueError:
                                pass
                                # print "Problem!!"
                    if (len(new_c_vals) == len(ref_ids)):
                        explode(new_c_vals, ref_ids, c, c_parent)
                    else:
                        # pass in production, print for debugging
                        pass
                        # print "# refids NE new_c_vals.\n refids: %s \n c_vals: %s \n" %(ref_ids, new_c_vals)

        """
        STEP 2
        Count bib-reference(s)
        Add an attribute to each cross-ref with the number of the bibliographic reference it denotes.
        """
        xpath_bib_references ="//ce:bib-reference"
        bib_refrences = tree.xpath(xpath_bib_references, namespaces={'ce' : 'http://www.elsevier.com/xml/common/dtd'})
        bib_ref_pos = 1
        for b in bib_refrences:
            b.set("positionNumber", str(bib_ref_pos))
            b_ref_id = b.attrib['id'].split()[0]
            xpath_cross_ref_bib_pointers = "//ce:cross-ref[@refid='{0}']".format(b_ref_id)

            cross_ref_bib_pointers = tree.xpath(xpath_cross_ref_bib_pointers, namespaces={'ce': 'http://www.elsevier.com/xml/common/dtd'})

            for c in cross_ref_bib_pointers:
                c.set("positionNumberOfBibliographicReference", str(bib_ref_pos))
            bib_ref_pos += 1

        """
        STEP 3
        Identify InTextPointer (by checking @positionNumberOfBibliographicReference attribute)
        - Add position attribute
        - Normalize cross-ref content, by substituting content with a marker
            - invokes buildTextualMarker()
        """
        xpath = "//ce:cross-ref[@positionNumberOfBibliographicReference]"
        cross_refs = tree.xpath(xpath, namespaces={'ce': 'http://www.elsevier.com/xml/common/dtd'})

        if len(cross_refs) == 0 :
                papers_with_no_crossrefs.append(f)

        current_cross_ref_pos = 1
        for c in cross_refs:
            c.set("positionNumber", str(current_cross_ref_pos))
            c_textual_marker = build_textual_marker(current_cross_ref_pos, c.attrib['positionNumberOfBibliographicReference'])

            try:
                c.text = c.text + c_textual_marker
            except TypeError:
                c.text = "" + c_textual_marker
                papers_with_block_detect_error.append(f)
                print "Rare typeError Happened", c.get('refid'), c_textual_marker_current

            current_cross_ref_pos += 1

        """
        STEP 4
        Extract citation contexts and build info array
        """
        c_ref_info = []
        xpath = "//ce:cross-ref[@positionNumberOfBibliographicReference]"
        cross_refs = tree.xpath(xpath, namespaces={'ce': 'http://www.elsevier.com/xml/common/dtd'})
        count = 0
        for c in cross_refs:
            current_ref_id = c.attrib['positionNumberOfBibliographicReference']
            c_ref_info_being_added = {}
            c_ref_info_being_added['positionNumber'] = c.attrib['positionNumber']
            c_ref_info_being_added['positionNumberOfBibliographicReference'] = current_ref_id
            c_textual_marker_current = build_textual_marker(c_ref_info_being_added['positionNumber'], current_ref_id)
            # print c_textual_marker_current

            xpath_block = "//*[self::ce:para or self::ce:entry or self::ce:note-para or self::ce:simple-para or self::ce:textref or self::xocs:item-toc-section-title or self::entry or self::ce:source or self::ce:section-title][descendant::ce:cross-ref[@positionNumberOfBibliographicReference and @positionNumber='{0}']]".format(c_ref_info_being_added['positionNumber'])
            connected = c.get("connected")

            block_containing_cross_ref = tree.xpath(xpath_block, namespaces=NMSPCS)
            if not connected:
                try:
                    block_content = et.tostring(block_containing_cross_ref[0], method="text", encoding="unicode")
                except IndexError:
                    block_content = ""
            else:
                if connected == "0":
                    try:
                        block_content = et.tostring(block_containing_cross_ref[0], method="text", encoding="unicode")
                    except IndexError:
                        block_content = ""
            candidate_sentences = sent_detector.tokenize(block_content.strip())

            marker_regexp = "\[xxxcitxxx\[\[_'(?P<pos>.*?)'_\]\[_'.*?'_\]\]xxxcitxxx\]"
            for i in range(len(candidate_sentences)):
                if c_textual_marker_current in candidate_sentences[i]:
                    citation_context = candidate_sentences[i]
                    ref_pointers = re.findall("\[_'.*?'_\]", citation_context)
                    first_ref_pointer = ref_pointers[0].strip("[]_'")
                    c_ref_info_being_added['sentenceid'] = "sentence-with-in-text-reference-pointer-"+first_ref_pointer
                    citation_context = re.sub(marker_regexp, "" , citation_context)
                    c_ref_info_being_added['citation_context'] = citation_context
                    c_ref_info_being_added['DEBUG-blockContent'] = block_content
            c_ref_info.append(c_ref_info_being_added)
            # print c_ref_info

        """
        STEP 5
        Convert to RDF
        """
        graph_of_citation_contexts = Graph()
        graph_of_citation_contexts.namespace_manager = ns_mgr
        work_uri = SEMLANCET_NS + eid # http://www.semanticlancet.eu/resource/1-s2.0-S157082680300009X
        exp_uri = work_uri + "/version-of-record" # http://www.semanticlancet.eu/resource/1-s2.0-S157082680300009X/version-of-record
        exp_resource = URIRef(exp_uri)

        for c in c_ref_info:
            # http://www.semanticlancet.eu/resource/1-s2.0-S157082680300009X/version-of-record/reference-list/NUMBER/reference
            ref_uri = URIRef(exp_uri + "/reference-list/" + c['positionNumberOfBibliographicReference'] + "/reference")
            # http://www.semanticlancet.eu/resource/1-s2.0-S157082680300009X/version-of-record/in-text-reference-pointer/positionNumber
            in_text_pointer_uri = URIRef(exp_uri + "/in-text-reference-pointer-" + c['positionNumber'])
            # http://www.semanticlancet.eu/resource/1-s2.0-S157082680300009X/version-of-record/sentenceid
            citation_sentence_uri = URIRef(exp_uri + "/" + c['sentenceid'])

            graph_of_citation_contexts.add( (in_text_pointer_uri, RDF.type, c4o.InTextReferencePointer) )
            graph_of_citation_contexts.add( (in_text_pointer_uri, c4o.hasContent, Literal("[" + c['positionNumberOfBibliographicReference'] + "]") ) )
            graph_of_citation_contexts.add( (in_text_pointer_uri, c4o.denotes, ref_uri) )

            graph_of_citation_contexts.add( (citation_sentence_uri, RDF.type, doco.Sentence) )
            graph_of_citation_contexts.add( (citation_sentence_uri, c4o.hasContent, Literal(c['citation_context'])) )
            graph_of_citation_contexts.add( (citation_sentence_uri, frbr.partOf, exp_resource) )
            graph_of_citation_contexts.add( (citation_sentence_uri, frbr.part, in_text_pointer_uri) )
            graph_of_citation_contexts.add( (exp_resource, frbr.part, citation_sentence_uri))

            graph_of_citation_contexts.add( (in_text_pointer_uri, c4o.hasContext, citation_sentence_uri) )
            graph_of_citation_contexts.add( (in_text_pointer_uri, frbr.partOf, citation_sentence_uri) )

        """
        STEP 6
        Serialize in a file
        """
        g_citation_filename = os.path.join(output_dir, eid + "." + RDF_EXTENSION )
        graph_of_citation_contexts.serialize(destination=g_citation_filename, format='turtle')
        number_of_papers += 1

        exec_t = time.time() - start_time
        print("--- in %s seconds ---\n" %exec_t)
        total_time = total_time + exec_t

        """"
        Summary
        TODO : add more information
        """
        summary_file = os.path.join(output_dir, SUMMARY_FILENAME)
        with open(summary_file, 'a') as sf:
            sf.write("\n" + f + "\n")
            for c in c_ref_info:
                citation_contexts_summary = c['positionNumber'] + " | " + c['positionNumberOfBibliographicReference'] + " | " + c['sentenceid'] + " | " + c["citation_context"] + " | " + c['DEBUG-blockContent'] + "\n"
                citation_contexts_summary = citation_contexts_summary.encode('ascii', 'ignore')
                #print citation_contexts_summary
                sf.write(citation_contexts_summary)
        sf.close()

        """
        In case we need to write the tree on a file
        """
        # tree.write("OUTPUT_FILE.XML", pretty_print=True)

if __name__ == "__main__":
    print "%d Papers have been processed" %number_of_papers
    print "Total execution time: %s seconds" %total_time
    print "%d papers with no cross-ref :\n" %len(papers_with_no_crossrefs)
    for p in papers_with_no_crossrefs:
        print "\t", p
    if papers_with_block_detect_error:
        print "\nBlock detection erros happened %d times" %len(papers_with_block_detect_error)
        for p in papers_with_block_detect_error:
            print "\t", p
    print "Removed %d cross-refs\nPreserve function used %d times" %(count_remove_all, count_remove_preserve)
