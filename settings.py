import re
import logging
from rdflib import Graph
from rdflib.namespace import Namespace, NamespaceManager
from lxml import etree as et
import nltk.data

# language to be used by nlptk
sent_detector = nltk.data.load('tokenizers/punkt/english.pickle')

# available logging for RDF
logging.basicConfig(level=logging.INFO)

# Global variables
SEMLANCET_NS = "http://www.semanticlancet.eu/resource/"
SEMLANCET_URI_PRO_ROLE_AUTHOR = "http://purl.org/spar/pro/author"
SUMMARY_FILENAME = "_CITATION_CONTEXTS_SUMMARY.csv"
REPORT_FILENAME = "_REPORT.txt"
NO_CROSS_REFS_LIST = "_NO_CROSS_REFS.txt"
RDF_EXTENSION = "ttl"
RDF_SERIALIZATION_FORMAT = "turtle"
NON_DECIMAL = re.compile(r'[^\d.]+')

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
