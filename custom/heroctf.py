from typing import List, Dict
from neo4j import GraphDatabase
from web3 import Web3
from web3.types import BlockData

from attributedict.collections import AttributeDict
from hexbytes import HexBytes

from utils import *

def heroctf(args):
	"""
	feel free to completly remove this function and change it to your needs !
	(remove it from the main function too !) its made for dev purpose but serves no real usage
	"""
	with GraphDatabase.driver(args.database, auth=(args.user, args.password)) as driver:
		with driver.session() as session:

			session.execute_write(submit, "match (n) detach delete n")

			transactions = []
			with open("./heroctftransactions") as f:
				for line in f.readlines():
					print(f"obtaining line {line}")
					eval(f"transactions.append({line})")
					# exit()
			for transaction in transactions:
				print(f"importing transaction {transaction.blockNumber}")
				session.execute_write(import_transaction, transaction)
			
			session.execute_write(submit, "MATCH (n {addr: '0xf6c0513FA09189Bf08e1329E44A86dC85a37c176'}) SET n:`Initial address`")
			session.execute_write(submit, "MATCH (n {addr: '0x54741632BE9F6E805b64c3B31f3e052e1eAe73e2'}) SET n:`Flag du 1st chall`")
			session.execute_write(submit, "MATCH (n {addr: '0x26F8A2D63B06D84121b35990ce8b7FEbac4Fe353'}) SET n:`Flag du 2nd chall`")
			session.execute_write(submit, "MATCH (n {addr: '0x80AF38eCD0dE67B02552A558cFD144a38D544160'}) SET n:`Flag du 3eme chall`")
			# last flag is the transaction hash going from 0x80 to 0x99 iirc
