from typing import List

from neo4j import GraphDatabase

from web3 import Web3
from web3.types import BlockData

from tempfile import mkstemp
from os import fdopen

import pickle

from utils import *

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

def importf(args):
	""" Responsible for the import functionality
	- Initiate a connection to the neo4j db
	- Verify the connection
	- Read the save file and pickle.loads a list of block
	- Iterate over every transaction in every block and call the importer
	"""
	with GraphDatabase.driver(args.database, auth=(args.user, args.password)) as driver:
		with driver.session() as session:

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

def deletedb(args):
	""" Simply delete all nodes """
	with GraphDatabase.driver(args.database, auth=(args.user, args.password)) as driver:
		with driver.session() as session:
			session.execute_write(submit, "match (n) detach delete n")
	print("Done")

def dev(args):
	from custom.heroctf import heroctf
	heroctf(args)

def main():
	args = argparse_wrapper()
	action_array = {
		"fetch": fetch,
		"import": importf,
		"delete": deletedb,
		"dev": dev
	}
	action_array[args.action](args)

if __name__ == "__main__":
	main()
