#!/usr/local/bin/python
# coding: latin-1
import logging
from pprint import pprint

import requests
from sklearn.base import TransformerMixin
from sklearn.feature_extraction.stop_words import ENGLISH_STOP_WORDS
from nltk.corpus import stopwords
import string
import re
from spacy.en import English
from collections import Counter

from common import Actions
from common.DataStructure import JSONSerializable


class LiteratureActions(Actions):
    FETCH='fetch'
    PROCESS= 'process'

parser = English()

# A custom stoplist
STOPLIST = set(stopwords.words('english') + ["n't", "'s", "'m", "ca"] + list(ENGLISH_STOP_WORDS))
ALLOWED_STOPLIST=set(('non'))
STOPLIST = STOPLIST-ALLOWED_STOPLIST
# List of symbols we don't care about
SYMBOLS = " ".join(string.punctuation).split(" ") + ["-----", "---", "...", "“", "”", "'ve"]

LABELS = {
    u'ENT': u'ENT',
    u'PERSON': u'ENT',
    u'NORP': u'ENT',
    u'FAC': u'ENT',
    u'ORG': u'ENT',
    u'GPE': u'ENT',
    u'LOC': u'ENT',
    u'LAW': u'ENT',
    u'PRODUCT': u'ENT',
    u'EVENT': u'ENT',
    u'WORK_OF_ART': u'ENT',
    u'LANGUAGE': u'ENT',
    u'DATE': u'DATE',
    u'TIME': u'TIME',
    u'PERCENT': u'PERCENT',
    u'MONEY': u'MONEY',
    u'QUANTITY': u'QUANTITY',
    u'ORDINAL': u'ORDINAL',
    u'CARDINAL': u'CARDINAL'
}


class PublicationFetcher(object):
    """
    Retireve data about a publication
    """
    _QUERY_BY_EXT_ID= '''http://www.ebi.ac.uk/europepmc/webservices/rest/search?pagesize=10&query=EXT_ID:{}&format=json&resulttype=core'''
    _QUERY_TEXT_MINED='''http://www.ebi.ac.uk/europepmc/webservices/rest/MED/{}/textMinedTerms//1/1000/json'''

    def __init__(self):
        self.logger = logging.getLogger(__name__)


    def get_publication(self, pub_id):
        r=requests.get(self._QUERY_BY_EXT_ID.format(pub_id))
        r.raise_for_status()
        result = r.json()['resultList']['result'][0]
        return result

    def get_epmc_text_mined_entities(self, pub_id):
        r = requests.get(self._QUERY_TEXT_MINED.format(pub_id))
        r.raise_for_status()
        if 'semanticTypeList' in r.json():
            result = r.json()['semanticTypeList']['semanticType']
            return result


class AnalisedPublication(JSONSerializable):

    def __init__(self,
                 pub_id = "",
                 title = "",
                 abstract = "",
                 authors = [],
                 year = None,
                 date = "",
                 journal = "",
                 full_text = "",
                 lemmas={},
                 noun_chunks={},
                 epmc_text_mined_entities = {},
                 epmc_keywords = [],
                 n_analysed_sentences = 1,
                 ):
        self.pub_id = pub_id
        self.title = title
        self.abstract = abstract
        self.authors = authors
        self.year = year
        self.date = date
        self.journal = journal
        self.full_text = full_text
        self.lemmas = lemmas
        self.noun_chunks = noun_chunks
        self.epmc_text_mined_entities = epmc_text_mined_entities
        self.epmc_keywords = epmc_keywords
        self.n_analysed_sentences = n_analysed_sentences



class PublicationAnalyser(object):
    def __init__(self, fetcher):
        self.fetcher = fetcher
        self.logger = logging.getLogger(__name__)


    def analyse_publication(self, text_to_parse=None, pub_id= None):
        pub = AnalisedPublication()
        if pub_id:
            pub_data = self.fetcher.get_publication(pub_id=pub_id)
            pub.epmc_text_mined_entities = self.fetcher.get_epmc_text_mined_entities(pub_id)
            text_to_parse = unicode(pub_data['title'] + ' ' + pub_data['abstractText'])
            pub.pub_id = pub_id
            pub.title = pub_data['title']
            pub.abstract = pub_data['abstractText']


        pub.lemmas, pub.noun_chunks, pub.n_analysed_sentences = self._spacy_analyser(text_to_parse)

        return pub


    def _spacy_analyser(self, abstract):
        #TODO: see code below
        pass


class Literature(object):

    def __init__(self,
                 es,
                 ):
        self.es = es

    def fetch(self):
        #TODO: load everything with a fetcher in parallel
        pub_ids = ['24523595',
                   '26784250',
                   '27409410',
                   '26290144',
                   '25787843',
                   '26836588',
                   '26781615',
                   '26646452',
                   '26774881',
                   '26629442',
                   ]
        pub_fetcher = PublicationFetcher()
        for pid in pub_ids:
            pub = pub_fetcher.get_publication(pid)
            print pub

    def process(self):
        #TODO: process everything with an analyser in parallel
        pub_ids = ['24523595',
                   '26784250',
                   '27409410',
                   '26290144',
                   '25787843',
                   '26836588',
                   '26781615',
                   '26646452',
                   '26774881',
                   '26629442',
                   ]

        # for t in [text, text2, text3, text4, text5, text6]:
        pub_fetcher = PublicationFetcher()
        for pid in pub_ids:
            pub = pub_fetcher.get_publication(pid)
            t = unicode(pub['title'] + ' ' + pub['abstractText'])
            print('*' * 80)
            pprint(t)
            tokens, parsedEx = tokenizeText(t)
            parsed_vector = transform_doc(parsedEx)
            tl = t.lower()
            sents_count = len(list(parsedEx.sents))
            ec = Counter()
            #    print('ENTITIES:')
            for e in parsedEx.ents:
                e_str = u' '.join(t.orth_ for t in e).encode('utf-8').lower()
                if ((not e.label_) or (e.label_ == u'ENT')) and not (e_str in STOPLIST) and not (e_str in SYMBOLS):
                    if e_str not in ec:
                        try:
                            ec[e_str] += tl.count(e_str)
                        except:
                            print(e_str)
                            #            print( e_str, e_str in STOPLIST)
                            #        print (e.label, repr(e.label_),  ' '.join(t.orth_ for t in e))
            print('FILTERED NOUN CHUNKS')
            for k, v in ec.most_common(50):
                print k, round(float(v) / sents_count, 3)

            mined_data = pub_fetcher.get_epmc_text_mined_entities(pid)
            print('EUROPEPMC TEXT MINING')
            if mined_data:
                for d in mined_data:
                    print(d['name'])
                    for i in d['tmSummary']:
                        print '\t', i['term'], i['dbName'], round(float(i['count']) / sents_count, 3)

# Every step in a pipeline needs to be a "transformer".
# Define a custom transformer to clean text using spaCy
class CleanTextTransformer(TransformerMixin):
    """
    Convert text to cleaned text
    """

    def transform(self, X, **transform_params):
        return [cleanText(text) for text in X]

    def fit(self, X, y=None, **fit_params):
        return self

    def get_params(self, deep=True):
        return {}


# A custom function to clean the text before sending it into the vectorizer
def cleanText(text):
    # get rid of newlines
    text = text.strip().replace("\n", " ").replace("\r", " ")

    # replace twitter @mentions
    mentionFinder = re.compile(r"@[a-z0-9_]{1,15}", re.IGNORECASE)
    text = mentionFinder.sub("@MENTION", text)

    # replace HTML symbols
    text = text.replace("&amp;", "and").replace("&gt;", ">").replace("&lt;", "<")

    # lowercase
    text = text.lower()

    return text


# A custom function to tokenize the text using spaCy
# and convert to lemmas
def tokenizeText(sample):
    # get the tokens using spaCy
    tokens_all = parser(unicode(sample))
    #    for t in tokens_all.noun_chunks:
    #        print(t, list(t.subtree))
    # lemmatize
    lemmas = []
    for tok in tokens_all:
        lemmas.append(tok.lemma_.lower().strip() if tok.lemma_ != "-PRON-" else tok.lower_)
    tokens = lemmas

    # stoplist the tokens
    tokens = [tok for tok in tokens if tok.encode('utf-8') not in STOPLIST]

    # stoplist symbols
    tokens = [tok for tok in tokens if tok.encode('utf-8') not in SYMBOLS]

    # remove large strings of whitespace
    while "" in tokens:
        tokens.remove("")
    while " " in tokens:
        tokens.remove(" ")
    while "\n" in tokens:
        tokens.remove("\n")
    while "\n\n" in tokens:
        tokens.remove("\n\n")
    filtered = []
    for tok in tokens_all:
        #        if tok.lemma_.lower().strip() in tokens and tok.pos_ in ['PROP', 'PROPN', 'VERB','NOUN']:
        if tok.lemma_.lower().strip() in tokens and tok.pos_ in ['PROP', 'PROPN', 'NOUN', 'ORG', 'FCA', 'PERSON']:
            filtered.append(tok)
            #        else:
            #            print(tok.lemma_.lower().strip(), tok.pos_ )
    c = Counter([tok.lemma_.lower().strip() for tok in filtered])
    sents_count = len(list(tokens_all.sents))
    print 'COMMON LEMMAS'
    for i in c.most_common(50):
        if i[1] > 1:
            print i[0], round(float(i[1]) / sents_count,3)
    return tokens, tokens_all


text = u'''Pancreatic cancer risk variant in LINC00673 creates a miR-1231 binding site and interferes with PTPN11 degradation.
Genome-wide association studies have identified several loci associated with pancreatic cancer risk; however, the mechanisms by which genetic factors influence the development
of
sporadic pancreatic cancer remain largely unknown. Here, by using genome-wide association analysis and functional characterization, we identify a long intergenic noncoding RNA
(lincRNA), LINC00673, as a potential tumor suppressor whose germline variation is associated with pancreatic cancer risk. LINC00673 is able to reinforce the interaction of
PTPN11
with PRPF19, an E3 ubiquitin ligase, and promote PTPN11 degradation through ubiquitination, which causes diminished SRC-ERK oncogenic signaling and enhanced activation of the
STAT1-dependent antitumor response. A G>A change at rs11655237 in exon 4 of LINC00673 creates a target site for miR-1231 binding, which diminishes the effect of LINC00673 in an
allele-specific manner and thus confers susceptibility to tumorigenesis. These findings shed new light on the important role of LINC00673 in maintaining cell homeostasis and how
its germline variation might confer susceptibility to pancreatic cancer.'''

text2 = u'''An increase in galectin-3 causes cellular unresponsiveness to IFN-γ-induced signal transduction and growth inhibition in gastric cancer cells.
Glycogen synthase kinase (GSK)-3β facilitates interferon (IFN)-γ signaling by inhibiting Src homology-2 domain-containing phosphatase (SHP) 2. Mutated phosphoinositide 3-kinase
(PI3K) and phosphatase and tensin homolog (PTEN) cause AKT activation and GSK-3β inactivation to induce SHP2-activated cellular unresponsiveness to IFN-γ in human gastric cancer
AGS cells. This study investigated the potential role of galectin-3, which acts upstream of AKT/GSK-3β/SHP2, in gastric cancer cells. Increasing or decreasing galectin-3 altered
IFN-γ signaling. Following cisplatin-induced galectin-3 upregulation, surviving cells showed cellular unresponsiveness to IFN-γ. Galectin-3 induced IFN-γ resistance independent of
its extracellular β-galactoside-binding activity. Galectin-3 expression was not regulated by PI3K activation or by a decrease in PTEN. Increased galectin-3 may cause GSK-3β
inactivation and SHP2 activation by promoting PDK1-induced AKT phosphorylation at a threonine residue. Overexpression of AKT, inactive GSK-3βR96A, SHP2, or active SHP2D61A caused
cellular unresponsiveness to IFN-γ in IFN-γ-sensitive MKN45 cells. IFN-γ-induced growth inhibition and apoptosis in AGS cells were observed until galectin-3 expression was
downregulated. These results demonstrate that an increase in galectin-3 facilitates AKT/GSK-3β/SHP2 signaling, causing cellular unresponsiveness to IFN-γ.'''

text3 = u'''Inhibition of SHP2 in basal-like and triple-negative breast cells induces basal-to-luminal transition, hormone dependency, and sensitivity to anti-hormone treatment.
The Src homology phosphotyrosyl phosphatase 2 (SHP2) is a positive effector of cell growth and survival signaling as well transformation induced by multiple tyrosine kinase
oncogenes. Since the basal-like and triple-negative breast cancer (BTBC) is characterized by dysregulation of multiple tyrosine kinase oncogenes, we wanted to determine the
importance of SHP2 in BTBC cell lines.Short hairpin RNA-based and dominant-negative expression-based SHP2 inhibition techniques were used to interrogate the functional importance
of SHP2 in BTBC cell biology. In addition, cell viability and proliferation assays were used to determine hormone dependency for growth and sensitivity to anti-estrogen
treatment.We show that inhibition of SHP2 in BTBC cells induces luminal-like epithelial morphology while suppressing the mesenchymal and invasive property. We have termed this
process as basal-to-luminal transition (BLT). The occurrence of BLT was confirmed by the loss of the basal marker alpha smooth muscle actin and the acquisition of the luminal
marker cytokeratin 18 (CK18) expression. Furthermore, the occurrence of BLT led to estrogen receptor alpha (ERα) expression, hormone dependency, and sensitivity to tamoxifen
treatment.Our data show that inhibition of SHP2 induces BLT, ERα expression, dependency on estrogen for growth, and sensitivity to anti-hormone therapy. Therefore, inhibition of
SHP2 may provide a therapeutic benefit in basal-like and triple-negative breast cancer.'''

text4 = u'''Increased Risk for Other Cancers in Addition to Breast Cancer for CHEK2*1100delC Heterozygotes Estimated From the Copenhagen General Population Study.
CHEK2 is a cell cycle checkpoint regulator, and the CHEK2*1100delC germline mutation leads to loss of function and increased breast cancer risk. It seems plausible that this
mutation could also predispose to other cancers. Therefore, we tested the hypothesis that CHEK2*1100delC heterozygosity is associated with increased risk for other cancers in
addition to breast cancer in the general population.We examined 86,975 individuals from the Copenhagen General Population Study, recruited from 2003 through 2010. The participants
completed a questionnaire on health and lifestyle, were examined physically, had blood drawn for DNA extraction, were tested for presence of CHEK2*1100delC using Taqman assays and
sequencing, and were linked over 1943 through 2011 to the Danish Cancer Registry. Incidences and risks of individual cancer types, including breast cancer, were calculated using
Kaplan-Meier estimates, Fine and Gray competing-risks regressions, and stratified analyses with interaction tests.Among 86,975 individuals, 670 (0.8%) were CHEK2*1100delC
heterozygous, 2,442 developed breast cancer, and 6,635 developed other cancers. The age- and sex-adjusted hazard ratio for CHEK2*1100delC heterozygotes compared with noncarriers
was 2.08 (95% CI, 1.51 to 2.85) for breast cancer and 1.45 (95% CI, 1.15 to 1.82) for other cancers. When stratifying for sex, the age-adjusted hazard ratios for other cancers were
1.54 (95% CI, 1.08 to 2.18) for women and 1.37 (95% CI, 1.01 to 1.85) for men (sex difference: P = .63). For CHEK2*1100delC heterozygotes compared with noncarriers, the age- and
sex-adjusted hazard ratios were 5.76 (95% CI, 2.12 to 15.6) for stomach cancer, 3.61 (95% CI, 1.33 to 9.79) for kidney cancer, 3.45 (95% CI, 1.09 to 10.9) for sarcoma, and 1.60
(95% CI, 1.00 to 2.56) for prostate cancer.CHEK2*1100delC heterozygosity is associated with 15% to 82% increased risk for at least some cancers in addition to breast cancer. This
information may be useful in clinical counseling of patients with this loss-of-function mutation.'''

text5 = u'''Elevated α-synuclein caused by SNCA gene triplication impairs neuronal differentiation and maturation in Parkinson's patient-derived induced pluripotent stem cells.
We have assessed the impact of α-synuclein overexpression on the differentiation potential and phenotypic signatures of two neural-committed induced pluripotent stem cell lines derived from a Parkinson's disease patient with a
triplication of the human SNCA genomic locus. In parallel, comparative studies were performed on two control lines derived from healthy individuals and lines generated from the patient iPS-derived neuroprogenitor lines infected
with a lentivirus incorporating a small hairpin RNA to knock down the SNCA mRNA. The SNCA triplication lines exhibited a reduced capacity to differentiate into dopaminergic or GABAergic neurons and decreased neurite outgrowth and
lower neuronal activity compared with control cultures. This delayed maturation phenotype was confirmed by gene expression profiling, which revealed a significant reduction in mRNA for genes implicated in neuronal differentiation
such as delta-like homolog 1 (DLK1), gamma-aminobutyric acid type B receptor subunit 2 (GABABR2), nuclear receptor related 1 protein (NURR1), G-protein-regulated inward-rectifier potassium channel 2 (GIRK-2) and tyrosine
hydroxylase (TH). The differentiated patient cells also demonstrated increased autophagic flux when stressed with chloroquine. We conclude that a two-fold overexpression of α-synuclein caused by a triplication of the SNCA gene is
sufficient to impair the differentiation of neuronal progenitor cells, a finding with implications for adult neurogenesis and Parkinson's disease progression, particularly in the context of bioenergetic dysfunction.'''

text6 = u'''Alpha-synuclein Toxicity in the Early Secretory Pathway: How It Drives Neurodegeneration in Parkinsons Disease.
Alpha-synuclein is a predominant player in the pathogenesis of Parkinson's Disease. However, despite extensive study for two decades, its physiological and pathological mechanisms remain poorly understood. Alpha-synuclein forms a
perplexing web of interactions with lipids, trafficking machinery, and other regulatory factors. One emerging consensus is that synaptic vesicles are likely the functional site for alpha-synuclein, where it appears to facilitate
vesicle docking and fusion. On the other hand, the dysfunctions of alpha-synuclein are more dispersed and numerous; when mutated or over-expressed, alpha-synuclein affects several membrane trafficking and stress pathways,
including exocytosis, ER-to-Golgi transport, ER stress, Golgi homeostasis, endocytosis, autophagy, oxidative stress, and others. Here we examine recent developments in alpha-synuclein's toxicity in the early secretory pathway
placed in the context of emerging themes from other affected pathways to help illuminate its underlying pathogenic mechanisms in neurodegeneration.'''


def represent_word(word):
    if word.like_url:
        return '%%URL|X'
    text = re.sub(r'\s', '_', word.text)
    tag = LABELS.get(word.ent_type_, word.pos_)
    if not tag:
        tag = '?'
    return text + '|' + tag


def transform_doc(doc):
    for ent in doc.ents:
        ent.merge(ent.root.tag_, ent.text, LABELS[ent.label_])
    for np in list(doc.noun_chunks):
        #        print (np, np.root.tag_, np.text, np.root.ent_type_)
        while len(np) > 1 and np[0].dep_ not in ('advmod', 'amod', 'compound'):
            np = np[1:]
        # print (np, np.root.tag_, np.text, np.root.ent_type_)

        np.merge(np.root.tag_, np.text, np.root.ent_type_)
    strings = []
    for sent in doc.sents:
        if sent.text.strip():
            strings.append(' '.join(represent_word(w) for w in sent if not w.is_space))
    if strings:
        return '\n'.join(strings) + '\n'
    else:
        return ''





# print(parsedEx)
# for token in parsedEx:
#    print(token.orth_, token.ent_type_ if token.ent_type_ != "" else "(not an entity)", token.pos_)
#
# print("-------------- entities only ---------------")
## if you just want the entities and nothing else, you can do access the parsed examples "ents" property like this:
# ents = list(parsedEx.ents)
# for entity in ents:
#    print(entity.label, entity.label_, ' '.join(t.orth_ for t in entity))
# print(STOPLIST)
