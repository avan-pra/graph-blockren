from __future__ import annotations

from typing import List
from neo4j import GraphDatabase, Transaction, Result
from web3 import Web3
from web3.types import BlockData
from tempfile import mkstemp
from os import fdopen

import hexbytes
import pickle
import argparse

class ChainGraph(GraphDatabase):
	pass

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

	sentence = "MERGE (f:Address {addr: $from_addr})"
	if transaction['to']:
		sentence += "MERGE (t:Address {addr: $to_addr})"
	else:
		sentence += "MERGE (t:Address:`Contract Creation` {addr: '0x0'})"
	sentence += "CREATE (f)-[:INTERACTED_WITH {" \

	for key, value in transaction.items():
		if type(value) == hexbytes.main.HexBytes:
			sentence += f"{key}: '{value.hex()}'"
		elif type(value) in [int, list]:
			sentence += f"{key}: {value}"
		else:
			sentence += f"{key}: '{value}'"
		if key != list(transaction)[-1]:
			sentence += ", "

	sentence += "}]->(t)"

	return list (
		tx.run(
			sentence, from_addr=transaction['from'], to_addr=transaction['to']
		)
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
	pass

if __name__ == "__main__":
	main()
