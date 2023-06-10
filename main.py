from __future__ import annotations

from typing import List, Dict
from neo4j import GraphDatabase, Transaction, Result
from web3 import Web3
from web3.types import BlockData
from tempfile import mkstemp
from os import fdopen

import hexbytes
import pickle
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


def fetch(args):
	""" Responsible for the fetch function
	- Connect to rpc endpoint
	- Verify the user inputed range
	- Fetch block in a list
	- Pickle them and write them to a file
	"""

	w3 = Web3(Web3.HTTPProvider(args.chain))
	if not w3.is_connected():
		raise BaseException("Could not connect to rpc url", w3)

	start, end = [int(i) for i in args.range.split('-')]
	if not start <= end:
		raise BaseException(f"block {start} is > to {end}")

	print(f"Fetching a total of {end - start + 1} block (from {start} to {end})")
	blocklist: List[BlockData] = []
	for blocknbr in range(start, end + 1):
		block = w3.eth.get_block(blocknbr, full_transactions=True)
		blocklist.append(block)

	fd, filename = mkstemp()
	with fdopen(fd, 'wb') as blockfile:
		print(f"Writing blocks to {filename}")
		pickledblocklist = pickle.dumps(blocklist)
		blockfile.write(pickledblocklist)

	print(f"Wrote {len(blocklist)} block (from {start} to {end}) to {filename}")

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

def importf(args):
	""" Responsible for the import functionality
	- Initiate a connection to the neo4j db
	- Verify the connection
	- Read the save file and pickle.loads a list of block
	- Iterate over every transaction in every block and call the importer
	"""
	with GraphDatabase.driver(args.database, auth=(args.user, args.password)) as driver:
		with driver.session() as session:

			session.execute_write(submit, "match (n) detach delete n")

			# if not driver.verify_connectivity():
			# 	raise BaseException(driver)
			# if not driver.verify_authentication():
			# 	raise BaseException(driver)
			print(f"Connected to {args.database}")

			blockfile = open(args.file, 'rb')
			blocklist: List[BlockData] = pickle.loads(blockfile.read())
			print(f"Importing {sum([len(block['transactions']) for block in blocklist])} transactions")
			for block in blocklist:
				session.execute_write(import_block, block)
				for transaction in block['transactions']:
					session.execute_write(import_transaction, transaction)
			print("Done")

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
	return parser.parse_args()

def main():
	args = argparse_wrapper()
	action_array = {
		"fetch": fetch,
		"import": importf
	}
	action_array[args.action](args)

if __name__ == "__main__":
	main()
