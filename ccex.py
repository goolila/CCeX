import os
import sys
import logging

from lxml import etree as et

import nltk.data
import re

from rdflib import Graph, URIRef, Literal
from rdflib.namespace import Namespace, NamespaceManager, RDF

import time
number_of_papers =0

# available logging for RDF
logging.basicConfig(level=logging.INFO)

# language to be used by nlptk
sent_detector = nltk.data.load('tokenizers/punkt/english.pickle')

#def
SEMLANCET_NS = "http://www.semanticlancet.eu/resource/"
SEMLANCET_URI_PRO_ROLE_AUTHOR = "http://purl.org/spar/pro/author"

SUMMARY_FILENAME = "CITATION_CONTEXTS_SUMMARY.csv"

RDF_EXTENSION = "ttl"
RDF_SERIALIZATION_FORMAT = "turtle"

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

def build_textual_marker(p_number, ref_id):
    # output : [xxxcitxxx[['.1.'] ['.24.']]xxxcitxxx]
    return "[xxxcitxxx[[_'" + str(p_number) + "'_][_'" + ref_id + "'_]]xxxcitxxx]"

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

files = os.listdir(input_dir)
total_time = 0

for f in files:
    # f = 1-s2.0-S157082680400006X-full.xml
    start_time = time.time()
    f_name, f_extension = os.path.splitext(f)
    if (f_extension == ".xml" and f_name[-5:] == "-full"):
        eid = f_name[0:-5] #1-s2.0-S157082680300009X
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
        cross_refs = tree.xpath(xpath, namespaces={'ce': 'http://www.elsevier.com/xml/common/dtd'})
        for c in cross_refs:
            c_parent = c.getparent()
            c_val = c.text.strip("[]")
            if c_val:
                c_vals = re.split(',|and', c_val)
                ref_ids = c.attrib['refid'].strip().split()
                if (len(c_vals) == len(ref_ids)):
                    i = 0
                    for r in ref_ids:
                        CE = "http://www.elsevier.com/xml/common/dtd"
                        NS_MAP = {'ce': CE}
                        tag = et.QName(CE, 'cross-ref')
                        exploded_cross_refs = et.Element(tag, refid=r, nsmap=NS_MAP)
                        exploded_cross_refs.text = "[" + c_vals[i] + "]" # ERRO GENERATOR
                        c.addprevious(exploded_cross_refs)
                        i += 1
                    c_parent.remove(c) # ERROR GENERATOR
                else:
                    print("# of refids is ne c_vals")
                    print "refid=[", c.attrib['refid'], "]"

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
            cross_ref_bib_pointers = tree.xpath(xpath_cross_ref_bib_pointers, namespaces=NMSPCS)

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

        current_cross_ref_pos = 1
        for c in cross_refs:
            c.set("positionNumber", str(current_cross_ref_pos))
            c_textual_marker = build_textual_marker(current_cross_ref_pos, c.attrib['positionNumberOfBibliographicReference'])

            text_to_recognize_citation = et.Element("tmarker")
            text_to_recognize_citation.text = c_textual_marker
            c.append(text_to_recognize_citation)

            current_cross_ref_pos += 1
        # output till here for first refid of first cross-refs pointing to bib24:
        # <ce:cross-ref refid="bib24" positionNumberOfBibliographicReference="24" positionNumber="1">[24]<tmarker>[xxxcitxxx[['.1.']['.24.']]xxxcitxxx]</tmarker></ce:cross-ref>
        # c.text( [24] ) can be removed.

        """
        STEP 4
        Extract citation contexts and build info array
        """


        xpath = "//ce:cross-ref[@positionNumberOfBibliographicReference]"
        cross_refs = tree.xpath(xpath, namespaces={'ce': 'http://www.elsevier.com/xml/common/dtd'})
        c_ref_info = []

        for c in cross_refs:
            current_ref_id = c.attrib['positionNumberOfBibliographicReference']
            c_ref_info_being_added = {}
            c_ref_info_being_added['positionNumber'] = c.attrib['positionNumber']
            c_ref_info_being_added['positionNumberOfBibliographicReference'] = current_ref_id
            c_textual_marker_current = build_textual_marker(c_ref_info_being_added['positionNumber'], current_ref_id)

            xpath_block = "//*[self::ce:para or self::ce:note-para or self::ce:simple-para or self::ce:textref or self::xocs:item-toc-section-title or self::entry or self::ce:source or self::ce:section-title][descendant::ce:cross-ref[@positionNumberOfBibliographicReference and @positionNumber='{0}']]".format(c_ref_info_being_added['positionNumber'])
            block_containing_cross_ref = tree.xpath(xpath_block, namespaces=NMSPCS)

            block_content = et.tostring(block_containing_cross_ref[0], method="text", encoding="unicode") # caused error on S1570826807000133, S1570826808000218

            """
            Tokenize sentences
            """
            candidate_sentences = sent_detector.tokenize(block_content.strip())
            # lazy * , output =  [xxxcitxxx[[_'2'_] [_'2'_]]xxxcitxxx] and (2) dynamic linking between pages based on the semantic relations in the underlying knowledge base [6][xxxcitxxx[[_'3'_] [_'6'_]]xxxcitxxx]
            # non lazy *? , output = only the first occurrance : [xxxcitxxx[[_'2'_] [_'2'_]]xxxcitxxx]
            marker_regexp = "\[xxxcitxxx\[\[_'(?P<pos>.*?)'_\]\[_'.*?'_\]\]xxxcitxxx\]"


            for i in range(len(candidate_sentences)):
                if c_textual_marker_current in candidate_sentences[i]:
                    citation_context = candidate_sentences[i]
                    ref_pointers = re.findall("\[_'.*?'_\]", citation_context)
                    first_ref_pointer = ref_pointers[0].strip("[]_'")
                    c_ref_info_being_added['sentence_id'] = "sentence-with-in-text-reference-pointer-"+first_ref_pointer[0].strip("[]_'")
                    # citation_context = re.sub(marker_regexp, r'\g<1>', citation_context)
                    citation_context = re.sub(marker_regexp, "" , citation_context)
                    c_ref_info_being_added['citation_context'] = citation_context
                    c_ref_info_being_added['DEBUG-blockContent'] = block_content
            c_ref_info.append(c_ref_info_being_added)
            print c_ref_info

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
            citation_sentence_uri = URIRef(exp_uri + "/" + c['sentence_id'])

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


        """
        Debug
        """

        """
        In case we need to write the tree on a file
        """
        # tree.write("OUTPUT_FILE.XML", pretty_print=True)

        """"
        Summary
        """
        for c in c_ref_info:
            citation_contexts_summary = c['positionNumber'] + "|" + c['positionNumberOfBibliographicReference'] + "|" + c['sentence_id'] + "|" + c['citation_context'] + "|" + c['DEBUG-blockContent']

    	summary_file = os.path.join(output_dir, SUMMARY_FILENAME)
    	f = open(summary_file, 'w')
    	f.write(citation_contexts_summary)
    	f.close()

if __name__ == "__main__":


    # STEP 0 : Open files, set directories
    # Initialize counters
    papers_with_no_crossrefs = 0
    # set and check input & output directories

    # print ("Input: %s\t is OK\nOutput: %s\tis OK" %(input_dir, output_dir))

    # functions to be added:
    check_permission(input_dir, output_dir)
    # Open all files in a loop, then for each f in files:
    # STEP 1:
    # expand_cross_refs(f)
    # STEP 2:
    # count_bib_ref(f)
    # STEP 3:
    # identify_intext_pointers(f)
    # STEP 4:
    # extract_citation_contexts(f)
    # STEP 5:
    # convert_to_RDF(f)

    print("%s Papers have been procced" %number_of_papers)
    print "Total execution time: %s" %total_time
