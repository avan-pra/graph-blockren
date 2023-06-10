from typing import List, Dict
from neo4j import Transaction
from web3.types import BlockData

import hexbytes
import argparse


class Neo4JUtility:
	@staticmethod
	def stringify_properties(properties: Dict[str, str]) -> str:
		sentence = ""
		for key, value in properties.items():
			if type(value) == hexbytes.main.HexBytes:
				sentence += f"{key}: '{value.hex()}'"
			elif type(value) in [list]:
				sentence += f"{key}: {value}"
			else:
				sentence += f"{key}: '{value}'"
			if key != list(properties)[-1]:
				sentence += ", "
		return sentence

	@staticmethod
	def create_node(labels: List[str], properties: Dict[str, str], alias="") -> str:

		labelsstr = ''.join([f":{label}" for label in labels])
		cleaned_properties = Neo4JUtility.stringify_properties(properties)

		return f"CREATE ({alias}{labelsstr} {{{cleaned_properties}}})"

	@staticmethod
	def merge_node(labels: List[str], properties: Dict[str, str], alias="") -> str:

		labelsstr = ''.join([f":{label}" for label in labels])
		cleaned_properties = Neo4JUtility.stringify_properties(properties)

		return f"MERGE ({alias}{labelsstr} {{{cleaned_properties}}})"

	@staticmethod
	def create_relationship(aliasfrom: str, labels: List[str], properties: Dict[str, str], aliasto) -> str:

		labelsstr = ''.join([f":{label}" for label in labels])
		cleaned_properties = Neo4JUtility.stringify_properties(properties)

		return f"CREATE ({aliasfrom})-[{labelsstr} {{{cleaned_properties}}}]->({aliasto})"

def submit(tx: Transaction, sentence: str):
	tx.run(sentence)

def import_transaction(tx: Transaction, transaction):
	"""
	Receive a web3 transaction create a cypher sentence and execute it.
	"""

	addrfrom = Neo4JUtility.merge_node(["Address"], {"addr": transaction['from']}, "f")
	if transaction['to']:
		addrto = Neo4JUtility.merge_node(["Address"], {"addr": transaction['to']}, "t")
	else:
		addrto = Neo4JUtility.merge_node(["Address", "`Contract Creation`"], {"addr": transaction['to']}, "t")

	relation = Neo4JUtility.create_relationship("f", ["INTERACTED_WITH"], transaction, "t")

	return list (
		tx.run(f"{addrfrom}{addrto}{relation}")
	)

def import_block(tx: Transaction, block: BlockData):

	block = dict(block)
	block.pop("transactions")
	block.pop("withdrawals")

	blocksentence = Neo4JUtility.create_node(["Block"], block, "t")
	minersentence = Neo4JUtility.merge_node(["Address"], {'addr': block['miner']}, "f")
	relation = Neo4JUtility.create_relationship("f", ["MINED"], {}, "t")
	return list (
		tx.run(f"{blocksentence}{minersentence}{relation}")
	)

def argparse_wrapper():
	parser = argparse.ArgumentParser(
		description='A tool to vizualize eth blockchain transaction using a graph database'
	)
	subparser = parser.add_subparsers(dest='action', required=True)
	fetch = subparser.add_parser('fetch', help='fetch blockchain data')
	fetch.add_argument('-c', '--chain', required=True, help='A chain URI (rpc url)')
	fetch.add_argument('-r', '--range', required=True, help='Block range to fetch (inclusive) example 3529374-3529379')
	db = subparser.add_parser('import', help='import collected data to database')
	db.add_argument('-d', '--database', help='neo4j database url', default='bolt://localhost:7687')
	db.add_argument('-f', '--file', help='file to parse', required=True)
	db.add_argument('--user', help='username for neo4j database', default='neo4j')
	db.add_argument('--password', help='password for neo4j database', default='password')
	deletedb = subparser.add_parser('delete', help='delete all nodes in your neo4j database')
	deletedb.add_argument('-d', '--database', help='neo4j database url', default='bolt://localhost:7687')
	deletedb.add_argument('--user', help='username for neo4j database', default='neo4j')
	deletedb.add_argument('--password', help='password for neo4j database', default='password')
	dev = subparser.add_parser('dev', help='want to run your own custom code ?')
	dev.add_argument('-d', '--database', help='neo4j database url', default='bolt://localhost:7687')
	dev.add_argument('--user', help='username for neo4j database', default='neo4j')
	dev.add_argument('--password', help='password for neo4j database', default='password')
	return parser.parse_args()
