'''Runs quality control queries on the database'''
import logging
from collections import Counter
from pprint import pprint

from elasticsearch import helpers

from common import Actions
from common.ElasticsearchQuery import ESQuery
from settings import Config


class QCActions(Actions):
    QC='qc'


def defauldict(param):
    pass


class QCRunner(object):

    def __init__(self, es):

        self.es = es
        self.esquery = ESQuery(es)

        self.run_associationQC()

    def run_associationQC(self):
        c=0
        e=0
        for ass_hit in helpers.scan(client=self.es,
                                    query={"query": {
                                        "match_all": {}
                                    },
                                        '_source': True,
                                        'size': 1000,
                                    },
                                    scroll='1h',
                                    doc_type=Config.ELASTICSEARCH_DATA_ASSOCIATION_DOC_NAME,
                                    index=Config().get_versioned_index(Config.ELASTICSEARCH_DATA_ASSOCIATION_INDEX_NAME),
                                    timeout="10m",
                                    ):
            c+=1
            if c %100 == 0:
                logging.info('%i association processed, %i errors found'%(c, e))

            ass = ass_hit['_source']
            ass_ev_counts = ass['evidence_count']['datasources']
            target, disease = ass['target']['id'], ass['disease']['id']
            db_ev_counts = self.count_evidence_sourceIDs(target, disease )

            for ds in ass_ev_counts:
                correct = ass_ev_counts[ds]==db_ev_counts[ds]
                if not correct:
                    logging.error("evidence count mismatch for association %s for datasource %s. association object:%i, evidence objects available:%i"%(ass['id'],ds, ass_ev_counts[ds], db_ev_counts[ds]))
                    e+=1
                    break
        logging.info('%i association processed, %i errors found' % (c, e))
        logging.info('DONE')

    def count_evidence_sourceIDs(self, target, disease):
        count = Counter()
        for ev_hit in helpers.scan(client=self.es,
                                    query={"query": {
                                              "filtered": {
                                                  "filter": {
                                                      "bool": {
                                                          "must": [
                                                              {"terms": {"target.id": [target]}},
                                                              {"terms": {"private.efo_codes": [disease]}},
                                                                    ]
                                                      }
                                                  }
                                              }
                                            },
                                           '_source': dict(include=['sourceID']),
                                           'size': 1000,
                                    },
                                    scroll = '1h',
                                    index = Config().get_versioned_index(Config.ELASTICSEARCH_DATA_INDEX_NAME+'*'),
                                    timeout = 60*10,
                                    ):
            count [ev_hit['_source']['sourceID']]+=1

        return count




